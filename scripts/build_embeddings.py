"""
Gemini 임베딩 인덱스 빌드 스크립트

- 모델: gemini-embedding-001 (다국어, 한국어 지원)
- 대상 노드: TermNode(definition 있는 것), RegNode
- 저장: data/rag/node_embeddings.pkl

free tier 한도: 1,000 embeddings/일
중간 저장 기능: 배치마다 node_embeddings_partial.pkl에 저장 -> 재실행 시 이어받기

실행:
  uv run python scripts/build_graph.py   # 먼저 그래프 빌드
  uv run python scripts/build_embeddings.py  # 임베딩 빌드 (여러 날에 걸쳐 실행 가능)
"""

import os
import pickle
import re
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
GRAPH_PATH = BASE_DIR / "data" / "rag" / "knowledge_graph.pkl"
EMBED_PATH = BASE_DIR / "data" / "rag" / "node_embeddings.pkl"
PARTIAL_PATH = BASE_DIR / "data" / "rag" / "node_embeddings_partial.pkl"

EMBED_MODEL = "models/gemini-embedding-001"
EMBED_TARGET_TYPES = {"TermNode", "RegNode"}  # ProductNode는 이름 매칭으로 충분
BATCH_SIZE = 50       # 배치당 텍스트 수
RATE_LIMIT_SLEEP = 2.0  # 배치 간 최소 대기 (초)


def _get_node_text(node_id: str, data: dict) -> str:
    name = data.get("name", "")
    node_type = data.get("node_type", "")

    if node_type == "TermNode":
        definition = data.get("definition", "")[:300]
        return f"{name} {definition}".strip()
    elif node_type == "RegNode":
        content = data.get("content", "")[:300]
        return f"{name} {content}".strip()

    return name


def _load_partial() -> dict:
    """이미 완료된 임베딩 로드 (resume용)

    우선순위:
    1. node_embeddings_partial.pkl (진행 중인 실행의 중간 저장)
    2. node_embeddings.pkl (이전 완료 결과 — 그래프 재빌드 후 재활용)
    3. {} 빈 딕셔너리 (처음 실행)
    """
    if PARTIAL_PATH.exists():
        with open(PARTIAL_PATH, "rb") as f:
            return pickle.load(f)

    if EMBED_PATH.exists():
        with open(EMBED_PATH, "rb") as f:
            index = pickle.load(f)
        # node_embeddings.pkl 포맷 → {node_id: embedding_vector} 딕셔너리로 변환
        return {nid: emb for nid, emb in zip(index["node_ids"], index["embeddings"])}

    return {}  # node_id -> embedding vector


def _save_partial(done: dict) -> None:
    with open(PARTIAL_PATH, "wb") as f:
        pickle.dump(done, f)


def build_embeddings(G) -> dict:
    import google.genai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    # 임베딩 대상 노드 수집 (definition 있는 TermNode + RegNode)
    all_nodes = []
    for node_id, data in G.nodes(data=True):
        node_type = data.get("node_type")
        if node_type not in EMBED_TARGET_TYPES:
            continue
        if node_type == "TermNode" and not data.get("definition", "").strip():
            continue
        text = _get_node_text(node_id, data)
        if text.strip():
            all_nodes.append((node_id, text))

    # 이미 완료된 노드 제외 (resume)
    done = _load_partial()
    remaining = [(nid, txt) for nid, txt in all_nodes if nid not in done]

    print(f"전체 대상: {len(all_nodes)}개")
    print(f"이미 완료: {len(done)}개")
    print(f"남은 작업: {len(remaining)}개")
    print(f"모델: {EMBED_MODEL}")

    if not remaining:
        print("모두 완료되었습니다. 최종 파일 생성 중...")
        _finalize(all_nodes, done)
        return

    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[batch_idx : batch_idx + BATCH_SIZE]
        batch_ids = [nid for nid, _ in batch]
        batch_texts = [txt for _, txt in batch]
        batch_num = batch_idx // BATCH_SIZE + 1

        print(f"  배치 {batch_num}/{total_batches} ({len(batch_texts)}개)...", end=" ", flush=True)

        for attempt in range(3):
            try:
                result = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch_texts,
                    config={"task_type": "RETRIEVAL_DOCUMENT"},
                )
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    m = re.search(r"retry in (\d+)", err_str)
                    wait = int(m.group(1)) + 5 if m else 65

                    # 일일 한도 초과 여부 확인
                    if "PerDay" in err_str:
                        print(f"\n일일 한도 초과. {len(done)}개 저장 후 종료.")
                        print(f"내일 재실행하면 {len(done)}개부터 이어받습니다.")
                        _save_partial(done)
                        sys.exit(0)

                    print(f"\n  Rate limit - {wait}초 대기 후 재시도...", end=" ", flush=True)
                    time.sleep(wait)
                    if attempt == 2:
                        _save_partial(done)
                        raise
                else:
                    _save_partial(done)
                    raise

        for nid, emb in zip(batch_ids, [e.values for e in result.embeddings]):
            done[nid] = emb

        # 배치마다 중간 저장
        _save_partial(done)
        print("완료")

        if batch_idx + BATCH_SIZE < len(remaining):
            time.sleep(RATE_LIMIT_SLEEP)

    print(f"\n전체 완료: {len(done)}개")
    _finalize(all_nodes, done)


def _finalize(all_nodes: list, done: dict) -> None:
    """partial 결과를 최종 node_embeddings.pkl로 변환"""
    node_ids = [nid for nid, _ in all_nodes if nid in done]
    embeddings = np.array([done[nid] for nid in node_ids], dtype=np.float32)

    index = {
        "node_ids": node_ids,
        "embeddings": embeddings,
        "model": EMBED_MODEL,
    }

    with open(EMBED_PATH, "wb") as f:
        pickle.dump(index, f)

    print(f"저장 완료: {EMBED_PATH}  shape={embeddings.shape}")

    # partial 파일 삭제 (완료 시)
    if PARTIAL_PATH.exists():
        PARTIAL_PATH.unlink()


if __name__ == "__main__":
    if not GRAPH_PATH.exists():
        print("knowledge_graph.pkl이 없습니다. 먼저 build_graph.py를 실행하세요.")
        sys.exit(1)

    with open(GRAPH_PATH, "rb") as f:
        G = pickle.load(f)

    print("=== Gemini 임베딩 인덱스 구축 시작 ===")
    build_embeddings(G)
