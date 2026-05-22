#!/usr/bin/env python3
"""
eval 결과 뷰어 — tool call 시퀀스 + 최종 응답 + 루브릭 점수를 함께 출력합니다.

사용법:
  uv run python scripts/show_eval_results.py              # 전체 최신 결과
  uv run python scripts/show_eval_results.py navigation   # evalset 필터링
  uv run python scripts/show_eval_results.py pension_tax
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

EVAL_HISTORY_DIR = Path(__file__).parent.parent / "app" / ".adk" / "eval_history"

STATUS = {1: "✅ PASS", 2: "❌ FAIL", 0: "⏭ SKIP"}
RUBRIC_KO = {
    "relevance": "관련성",
    "helpfulness": "유용성",
    "tone_compliance": "말투",
    "no_product_recommendation": "가드레일",
    "literacy_level_appropriate": "리터러시",
}


def load_latest(evalset_filter: str | None) -> dict:
    """각 eval_id별 최신 결과 하나씩만 반환."""
    latest: dict[str, tuple[float, dict, str]] = {}

    for f in sorted(EVAL_HISTORY_DIR.glob("*.evalset_result.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        eval_set_id: str = data.get("eval_set_id", "")
        if evalset_filter and evalset_filter not in eval_set_id:
            continue

        ts_raw = f.stem.split("_eval_")[1].split(".evalset_result")[0]
        ts = float(ts_raw)
        for case in data.get("eval_case_results", []):
            eid = case.get("eval_id", "")
            if eid not in latest or ts > latest[eid][0]:
                latest[eid] = (ts, case, eval_set_id)

    return latest


def _text(parts: list) -> str:
    return " ".join(p.get("text", "") for p in parts if p.get("text"))


def print_case(case: dict, eval_set_id: str) -> None:
    eid = case.get("eval_id", "?")
    status = STATUS.get(case.get("final_eval_status", 0), "?")

    overall = case.get("overall_eval_metric_results") or []
    score_str = ""
    if overall:
        s = overall[0].get("score")
        score_str = f"  score={s:.2f}" if s is not None else ""

    print(f"\n{'='*72}")
    print(f"  {status}  {eid}{score_str}")
    print(f"  evalset: {eval_set_id}")
    print(f"{'='*72}")

    for inv_idx, inv in enumerate(case.get("eval_metric_result_per_invocation", []), 1):
        actual = inv.get("actual_invocation", {})

        user_text = _text(actual.get("user_content", {}).get("parts", []))
        if user_text:
            print(f"\n  [{inv_idx}] 👤  {user_text}")

        # tool calls
        events = actual.get("intermediate_data", {}).get("invocation_events", [])
        for ev in events:
            for part in ev.get("content", {}).get("parts", []):
                fc = part.get("function_call")
                fr = part.get("function_response")
                if fc:
                    args = ", ".join(f"{k}={v}" for k, v in (fc.get("args") or {}).items())
                    print(f"       🔧 {fc['name']}({args})")
                if fr:
                    resp = fr.get("response", {})
                    snippet = str(resp)[:150].replace("\n", " ")
                    print(f"          ↳ {snippet}")

        # final response
        final_text = _text(actual.get("final_response", {}).get("parts", []))
        if final_text:
            truncated = final_text[:280] + ("…" if len(final_text) > 280 else "")
            print(f"       🤖  {truncated}")

        # per-invocation rubric scores
        metric_results = inv.get("eval_metric_results") or []
        if metric_results:
            rubrics = metric_results[0].get("details", {}).get("rubric_scores", [])
            if rubrics:
                parts_str = []
                for r in rubrics:
                    label = RUBRIC_KO.get(r["rubric_id"], r["rubric_id"])
                    s = r.get("score", "?")
                    icon = "✓" if s == 1.0 else ("△" if isinstance(s, float) and s >= 0.5 else "✗")
                    parts_str.append(f"{label}{icon}{s}")
                print(f"       📊  {' | '.join(parts_str)}")


def main() -> None:
    # 인자 없으면 현행 3개 셋(bf_)만 표시 — 삭제된 구 evalset 히스토리 제외
    evalset_filter = sys.argv[1] if len(sys.argv) > 1 else "bf_"
    results = load_latest(evalset_filter)

    if not results:
        print("결과 없음. make eval 실행 후 다시 시도하세요.")
        return

    by_set: dict[str, list] = defaultdict(list)
    for eid, (_, case, esid) in sorted(results.items()):
        by_set[esid].append((eid, case))

    total_pass = sum(1 for _, case, _ in results.values() if case.get("final_eval_status") == 1)

    for esid, cases in sorted(by_set.items()):
        set_pass = sum(1 for _, c in cases if c.get("final_eval_status") == 1)
        print(f"\n\n{'#'*72}")
        print(f"#  {esid}  ({set_pass}/{len(cases)} PASS)")
        print(f"{'#'*72}")
        for _, case in cases:
            print_case(case, esid)

    print(f"\n\n{'='*72}")
    print(f"  총 결과: {total_pass}/{len(results)} PASS")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
