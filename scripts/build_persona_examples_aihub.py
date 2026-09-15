"""AI Hub "금융분야 고객상담 데이터"(NIA, 은행) → 페르소나 라우팅용 퓨샷 예시 생성.

목적: data/source/25.금융분야 고객상담 데이터/.../TS_은행.zip 안의 실제 은행 상담
      전화 대화(TX=상담사/RX=고객)에서, 연령대로 근사한 페르소나별 고객 발화를
      압축 해제 없이 zip에서 직접 스트리밍 추출한다.

추출·선별 모두 규칙 기반이다 (LLM 미사용):
- 페르소나 라벨은 데이터의 client_age 필드로 정함 (추론 아님)
- 대표 발화는 무작위 샘플링으로 뽑음 — "말투 특성"을 기준으로 LLM에게 고르게 하면
  그 기준(예: "고령층=디지털 용어에 낯섦")에 맞는 것만 골라 고정관념을 강화하는
  선별 편향이 생길 수 있어 의도적으로 배제했다.

주의: 산출물(data/personas/few_shot_examples.json)은 AI Hub 이용정책 확인 전까지
      .gitignore 처리돼 있음 — 커밋하지 말 것.

주부 페르소나는 이 데이터셋에 식별 필드가 없어 제외한다 (연령/성별만 제공됨).

사용법:
    uv run python scripts/build_persona_examples_aihub.py
"""
from __future__ import annotations

import json
import random
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ZIP_PATH = Path(
    "data/source/25.금융분야 고객상담 데이터/3.개방데이터/2.데이터(NIA)"
    "/Training/01.원천데이터/TS_은행.zip"
)
OUT_DIR = Path("data/personas")
FEWSHOT_FILE = OUT_DIR / "few_shot_examples.json"

RX_LINE = re.compile(r"^RX\s+(.+)$", re.MULTILINE)
SEED = 0

# ── 페르소나 설정 (주부 제외) ────────────────────────────────────────────────
PERSONA_CONFIG: dict[str, dict] = {
    "고령층":   {"target": 10, "age_buckets": {"60~69세", "70~79세", "80세이상"}},
    "중장년":   {"target": 8,  "age_buckets": {"40~49세", "50~59세"}},
    "직장인":   {"target": 8,  "age_buckets": {"30~39세"}},
    "사회초년생": {"target": 6,  "age_buckets": {"20~29세"}},
}


def extract_candidates() -> dict[str, list[str]]:
    """zip을 압축 해제하지 않고 스트리밍으로 읽어 페르소나별 RX 발화 후보를 모은다."""
    by_persona: dict[str, list[str]] = {p: [] for p in PERSONA_CONFIG}
    age_to_persona = {
        age: persona
        for persona, cfg in PERSONA_CONFIG.items()
        for age in cfg["age_buckets"]
    }

    with zipfile.ZipFile(ZIP_PATH) as z:
        names = [n for n in z.namelist() if n.endswith(".json")]
        for n in names:
            with z.open(n) as f:
                d = json.load(f)
            age = d["source"].get("client_age", "")
            persona = age_to_persona.get(age)
            if not persona:
                continue
            content = d["source"].get("consulting_content", "")
            for utt in RX_LINE.findall(content):
                utt = utt.strip()
                if 15 <= len(utt) <= 150 and "?" in utt:
                    by_persona[persona].append(utt)

    for p, utts in by_persona.items():
        print(f"  {p}: 후보 {len(utts)}개")
    return by_persona


def dedup(utterances: list[str]) -> list[str]:
    """공백·문장부호를 무시한 정규화 기준으로 거의 동일한 발화를 제거."""
    seen: set[str] = set()
    unique: list[str] = []
    for u in utterances:
        key = re.sub(r"[^\w가-힣]", "", u)
        if key in seen:
            continue
        seen.add(key)
        unique.append(u)
    return unique


def sample_examples(persona: str, candidates: list[str]) -> list[dict]:
    """무작위 샘플링으로 target개를 뽑는다. LLM 미사용, 말투 기준 필터 없음."""
    target = PERSONA_CONFIG[persona]["target"]
    rng = random.Random(SEED)
    pool = dedup(candidates)
    rng.shuffle(pool)
    chosen = pool[:target]
    return [{"persona": persona, "utterance": u} for u in chosen]


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== AI Hub 은행 상담 데이터에서 후보 추출 ===")
    candidates = extract_candidates()

    print("\n=== 무작위 샘플링 ===")
    final: list[dict] = []
    for persona in PERSONA_CONFIG:
        if not candidates[persona]:
            print(f"  {persona}: 후보 없음, 건너뜀")
            continue
        selected = sample_examples(persona, candidates[persona])
        print(f"  {persona}: {len(selected)}개 선택")
        final.extend(selected)

    FEWSHOT_FILE.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 저장 완료: {FEWSHOT_FILE} ({len(final)}개) ===")
