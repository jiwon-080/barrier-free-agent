"""
GraphRAG 검색 엔진

사용자 쿼리 → Gemini 임베딩 유사도 검색 → BFS multi-hop 탐색 → 통합 응답

탐색 우선순위:
  1. 정확 이름 매칭 (term_IRP)
  2. 부분 문자열 매칭
  3. Gemini text-multilingual-embedding-002 코사인 유사도
"""

import os
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

BASE_DIR = Path(__file__).parent.parent
GRAPH_PATH = BASE_DIR / "data" / "rag" / "knowledge_graph.pkl"
EMBED_PATH = BASE_DIR / "data" / "rag" / "node_embeddings.pkl"

EMBED_MODEL = "models/gemini-embedding-001"
EMBED_SIMILARITY_THRESHOLD = 0.75  # 이 점수 미만이면 임베딩 매칭 결과 버림


@lru_cache(maxsize=1)
def _load_graph():
    if not GRAPH_PATH.exists():
        return None
    with open(GRAPH_PATH, "rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=1)
def _load_embedding_index() -> Optional[dict]:
    if not EMBED_PATH.exists():
        return None
    with open(EMBED_PATH, "rb") as f:
        return pickle.load(f)


def _embed_query(query: str) -> Optional[np.ndarray]:
    """쿼리를 Gemini로 임베딩합니다."""
    try:
        import google.genai as genai
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=[query],
            config={"task_type": "RETRIEVAL_QUERY"},
        )
        return np.array(result.embeddings[0].values, dtype=np.float32)
    except Exception:
        return None


def _find_start_nodes(query: str, G, top_k: int = 3) -> list[str]:
    """
    쿼리와 가장 관련 높은 노드 ID 목록 반환.
    1) 정확 이름 매칭
    2) 부분 문자열 매칭
    3) 임베딩 유사도 (FAISS 없이 numpy 코사인)
    """
    candidates = []

    # 1) 정확 매칭
    exact_id = f"term_{query}"
    if G.has_node(exact_id):
        candidates.append(exact_id)
        if len(candidates) >= top_k:
            return candidates

    # 2) 부분 매칭 (이름이 있는 노드만, 빈 문자열 제외)
    query_lower = query.lower()
    for node_id, data in G.nodes(data=True):
        if node_id in candidates:
            continue
        name = data.get("name", "").lower()
        if not name:
            continue
        if query_lower in name or name in query_lower:
            candidates.append(node_id)
            if len(candidates) >= top_k:
                return candidates

    # 3) 임베딩 유사도
    if len(candidates) < top_k:
        index = _load_embedding_index()
        q_vec = _embed_query(query)
        if index is not None and q_vec is not None:
            embs = index["embeddings"]  # (N, D)
            norms = np.linalg.norm(embs, axis=1) * np.linalg.norm(q_vec) + 1e-9
            scores = embs @ q_vec / norms
            top_indices = np.argsort(scores)[::-1]

            for i in top_indices:
                if scores[i] < EMBED_SIMILARITY_THRESHOLD:
                    break  # 유사도 낮으면 이후 결과도 버림
                nid = index["node_ids"][i]
                if nid not in candidates:
                    candidates.append(nid)
                    if len(candidates) >= top_k:
                        break

    return candidates


def graph_search(query: str, depth: int = 2) -> dict:
    """
    쿼리로 시작 노드를 찾고 depth 홉까지 탐색하여 관련 정보를 반환합니다.

    Args:
        query: 사용자 검색어 (예: "IRP", "세액공제", "ETF")
        depth: 탐색 홉 수 (기본 2)

    Returns:
        {
            "matched_term": str | None,
            "definition": str,
            "related_terms": list[str],
            "suggested_route": str | None,    # navigation_tool route_key
            "regulation_hint": str | None,    # 관련 규정 내용
            "guardrail": bool,                # True면 고위험 상품 경고
            "products": list[str],            # 관련 상품명
            "macro_related": list[str],       # 관련 거시경제 지표
        }
    """
    G = _load_graph()
    if G is None:
        return _empty_result()

    start_nodes = _find_start_nodes(query, G)
    if not start_nodes:
        return _empty_result()

    primary = start_nodes[0]
    node_data = G.nodes[primary]

    result = {
        "matched_term": node_data.get("name"),
        "definition": node_data.get("definition") or node_data.get("content") or "",
        "related_terms": [],
        "suggested_route": None,
        "regulation_hint": None,
        "guardrail": False,
        "products": [],
        "macro_related": [],
    }

    # 시작 노드 이름 집합 (related_terms 자기참조 방지)
    start_names = {G.nodes[nid].get("name", "") for nid in start_nodes}

    # BFS multi-hop 탐색
    visited = set(start_nodes)
    queue = [(nid, 0) for nid in start_nodes]

    while queue:
        current, hop = queue.pop(0)
        if hop >= depth:
            continue

        for neighbor in G.successors(current):
            edge = G.edges[current, neighbor]
            relation = edge.get("relation", "")
            ndata = G.nodes[neighbor]
            ntype = ndata.get("node_type", "")

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, hop + 1))

            if relation == "RELATED_TO" and ntype == "TermNode":
                name = ndata.get("name", "")
                # 자기 자신(시작 노드) 제외
                if name and name not in start_names and name not in result["related_terms"]:
                    result["related_terms"].append(name)

            elif relation in ("LEADS_TO", "TRIGGERS_GUARDRAIL") and ntype == "RouteNode":
                if not result["suggested_route"]:
                    result["suggested_route"] = ndata.get("route_key")
                if relation == "TRIGGERS_GUARDRAIL":
                    result["guardrail"] = True

            elif relation == "GOVERNED_BY" and ntype == "RegNode":
                if not result["regulation_hint"]:
                    hint = ndata.get("content", "")
                    # definition과 동일한 내용이면 중복 방지
                    if hint != result["definition"]:
                        result["regulation_hint"] = hint

            elif relation == "HAS_PRODUCT" and ntype == "ProductNode":
                name = ndata.get("name", "")
                if name and name not in result["products"]:
                    result["products"].append(name)

            elif relation == "AFFECTS" and ntype == "TermNode":
                name = ndata.get("name", "")
                if name and name not in result["macro_related"]:
                    result["macro_related"].append(name)

    # MacroNode도 역방향으로 확인 (TermNode → AFFECTS → MacroNode 방향 역추적)
    for predecessor in G.predecessors(primary):
        pdata = G.nodes[predecessor]
        if pdata.get("node_type") == "MacroNode":
            name = pdata.get("name", "")
            if name and name not in result["macro_related"]:
                result["macro_related"].append(name)

    # 관련 용어 최대 5개로 제한
    result["related_terms"] = result["related_terms"][:5]

    return result


def _empty_result() -> dict:
    return {
        "matched_term": None,
        "definition": "",
        "related_terms": [],
        "suggested_route": None,
        "regulation_hint": None,
        "guardrail": False,
        "products": [],
        "macro_related": [],
    }
