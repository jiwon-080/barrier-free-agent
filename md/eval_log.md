# Eval 변경 로그

eval을 돌릴 때마다 무엇을 바꿨고 결과가 어떻게 달라졌는지 기록합니다.

---

## Run 1 — 2026-04-29 | baseline (18/18 PASS)

**목적**: safety net 제거 전 기준선 측정

**변경 없음** (baseline)

**결과**: 18/18 PASS

**의의**: safety net이 있는 상태에서 모든 케이스 통과 확인.

---

## Run 2 — 2026-04-29 | safety net 제거 (17/18)

**목적**: `run_agent()` 안의 rule-based safety net 제거 후 LLM 자체 성능 측정

**제거한 코드** (`ui/demo.py`):
```python
# 삭제된 블록 — 가입 키워드 감지 시 navigate_ui 강제 호출
if not _nav_called:
    _NAV_KW = ["가입", "만들", "개설", "시작", "하고 싶", "할래", "원해", "신청"]
    if _irp_called and any(kw in query for kw in _NAV_KW):
        _auto = navigate_ui("IRP 신규가입")  ...
    elif _isa_called and any(kw in query for kw in _NAV_KW):
        _auto = navigate_ui("ISA 신규가입")  ...
```
- `_irp_called`, `_isa_called`, `_nav_called` 추적 변수도 함께 제거

**결과**: 17/18 PASS

| 케이스 | 결과 | 원인 |
|---|---|---|
| `irp_signup_full_flow` | ✅ PASS | LLM이 safety net 없이도 get_irp_info + navigate_ui 자발 호출 |
| `isa_signup_full_flow` | ✅ PASS | 동일 |
| `irp_term_explanation` | ❌ FAIL | 아래 참고 |

**실패 분석 — `irp_term_explanation`**:

원인 — `no_product_recommendation` rubric score 0.0
- `financial_advisor_agent`가 "추천합니다" 표현을 응답에 포함
- 새로 추가한 rubric이 잡아낸 실제 품질 문제
- (`tool_trajectory_avg_precision` score None도 관측됐으나 이 메트릭은 pass/fail에 미포함 — 별개 이슈)

**결론**:
- safety net 제거 성공 — 핵심 시나리오(IRP/ISA 가입 풀플로우)는 LLM이 자력으로 처리
- 실패 1건은 safety net과 무관한 rubric 품질 이슈

---

## Run 3 — 2026-04-30 | 추천 표현 금지 + eval case 수정 + dotenv fix (18/18 PASS)

**목적**: Run 2 실패 케이스 수정 후 18/18 복원

**변경 내용**:

1. `app/agent.py` — `financial_advisor_agent` instruction 추가:
   ```
   "추천합니다", "추천드립니다", "사용해 보세요" 등 권유 표현은 어떤 맥락에서도 사용하지 마세요.
   ```

2. `tests/eval/evalsets/basic.evalset.json` — tool_uses 수정 (멀티에이전트 구조 반영):
   - `irp_term_explanation`: `explain_financial_term` → `financial_advisor_agent`
   - `etf_term_explanation`: `explain_financial_term` → `financial_advisor_agent`
   - `isa_term_explanation`: `explain_financial_term` → `financial_advisor_agent`
   - `irp_alias_phonetic`: `explain_financial_term` → `financial_advisor_agent`

3. `app/__init__.py` — `load_dotenv(override=True)` 추가:
   - Windows 전역 환경변수(구 API key)가 `.env`보다 우선하는 문제 해결
   - `pyproject.toml`에 `python-dotenv>=1.0.0` 의존성 추가
   - 프로덕션(Cloud Run/Streamlit) 배포 시 `.env` 없으면 no-op이라 안전

**결과**: 18/18 PASS

**의의**: safety net 완전 제거 상태에서 18/18 복원 확인. LLM 자력으로 전 케이스 처리.

---

## 메트릭 설명

| 메트릭 | 설명 | threshold |
|---|---|---|
| `rubric_based_final_response_quality_v1` | LLM-as-judge 4개 rubric 평균 | 0.8 |
| ↳ `relevance` | 질문에 직접 답했는가 | — |
| ↳ `helpfulness` | 유용한 정보를 제공했는가 | — |
| ↳ `tone_compliance` | 합쇼체(~입니다/합니다) 준수 | — |
| ↳ `no_product_recommendation` | 투자 추천 표현 없는가 | — |
| `tool_trajectory_avg_precision` | 기대 도구 호출 순서 일치율 | — (참고용, pass/fail 미적용) |

## 설계 원칙 (배운 것)

- **멀티에이전트 eval**: outer 에이전트(`barrier_free_agent`) 시점의 tool_uses만 관측됨. sub-agent 내부 호출(`explain_financial_term`)은 보이지 않으므로 eval case는 `financial_advisor_agent`로 기대값 설정.
- **tool_trajectory_avg_precision 한계**: 멀티에이전트 구조에서 outer 도구만 관측 가능하고 LLM 호출 순서가 non-deterministic해서 신뢰도가 낮음. `eval_config.json`에 미포함 — 계산은 되지만 pass/fail 판정에 영향 없음. 참고용으로만 활용.
- **safety net 측정**: `irp_signup_full_flow` / `isa_signup_full_flow` 케이스가 safety net 제거 후에도 PASS이면 LLM이 자력 처리 가능하다는 증거.
- **rubric 추가 시**: 기존 통과 케이스가 새 rubric에서 실패할 수 있음 → 추가 후 full run 필수.
