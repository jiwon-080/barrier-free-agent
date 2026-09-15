# barrier-free-agent

디지털 금융 소외 계층을 위한 배리어프리 금융 에이전트.  
고령층·사회초년생·주부 등 페르소나를 자동 감지해 맞춤형 금융 상담, 앱 화면 이동, 절세 플래닝을 멀티에이전트 구조로 제공합니다.

> 구현 예시는 국내 모바일 뱅킹 앱을 기반으로 작성되었습니다.

---

## 아키텍처

```
[사용자]
    │
    ▼
_before_agent_callback  (callbacks.py)
  ① 사용자 메모리 로드 — 투자성향·금융이해도·관심상품 (세션 최초 1회)
  ② 페르소나 자동 감지 — LLM 분류(기준 프롬프트+퓨샷) → 고령층/사회초년생/직장인/중장년
  ③ 에이전트 스킬 메모리 동적 로드 → agent_skills 상태 주입
  ④ user_profile_summary 구성 (페르소나 힌트 + 투자성향 + 금융이해도)
    │
    ▼
barrier_free_financial_agent  뭉치 🐕  (오케스트레이터 — agent.py)
│  직접 도구: navigate_ui / get_isa_info / get_irp_info
│             set_user_profile / request_terms_analysis / check_investment_guardrail
│
├── [sub_agent] investment_agent      나비 🐱
│   도구: explain_financial_term, check_investment_guardrail,
│        search_products, get_product_detail, compare_products,
│        get_etf_price, get_etf_prices_by_keyword, get_macro_indicators,
│        simulation_agent(AgentTool), append_skill
│   지식베이스: glossary/ + investment/
│
├── [sub_agent] pension_tax_agent     까치 🐦
│   도구: get_irp_info, get_isa_info, simulation_agent(AgentTool), append_skill
│   지식베이스: pension_tax/
│
└── [sub_agent] fraud_detection_agent 호야 🐯
    도구: check_fraud_pattern, append_skill
    지식베이스: fraud/

[위임 전용 AgentTool — 사용자에게 직접 노출 안 됨]
simulation_agent  토리 🐿️
  도구: calculate_tax_saving, calculate_maturity_amount, calculate_pension_payout

[관리자 전용 앱 — barrier_free_agent와 별도 실행]
admin_app   → customer_management_agent  사용자 프로필 조회·삭제·통계
curator_app → system_improvement_agent   스킬 문서 큐레이션·중복 정리
```

---

## 페르소나 라우팅

첫 번째 발화에서 LLM이 페르소나 기준 프롬프트(`_PERSONA_ROUTING_PROMPT`) + 퓨샷 예시를 참고해 페르소나를 자동 분류합니다.  
분류 결과는 `user:persona` 상태에 저장되고, `user_profile_summary`를 통해 에이전트 안내 방식에 반영됩니다.

| 페르소나 | 감지 기준 | 안내 조정 |
|---------|---------|---------|
| 고령층 | 60대+, 구어체, 연금·손주 언급 | 쉬운 단어, 큰글 모드 안내 |
| 사회초년생 | 20대, 알바·주린이·청년 상품 | 기초 개념, 청년 전용 상품 우선 |
| 직장인 | 연말정산·4대보험·퇴직금 | 근로소득 절세 중심 |
| 중장년 | 40~50대, 노후 준비 시작 | 은퇴 기간 고려 플랜 |

분류 기준은 `app/callbacks.py`의 `_PERSONA_ROUTING_PROMPT`에 페르소나별 특성으로 정의돼 있습니다.  
"주부"는 이전 버전에 있었으나, 근거로 쓰던 네이버 지식iN 수집 데이터가 API 약관 위반으로 제거되며 함께 빠졌습니다
(대체용 AI Hub 데이터엔 주부를 식별할 필드가 없음).

**퓨샷 예시**: `data/source/`의 AI Hub "금융분야 고객상담 데이터"(NIA, 은행 상담 전화 텍스트)에서
`client_age`로 연령대를 근사해 페르소나를 매기고, `scripts/build_persona_examples_aihub.py`로 실제
고객 발화(RX 턴)를 무작위 샘플링합니다 — LLM이 "말투가 그럴듯한 것"을 고르게 하면 고정관념을 강화하는
선별 편향이 생길 수 있어 규칙 기반(정규식 추출 + 무작위 샘플링)만 씁니다.
산출물(`data/personas/few_shot_examples.json`)은 AI Hub 이용정책 확인 전까지 `.gitignore` 처리되어
로컬에만 존재하며 저장소에는 커밋되지 않습니다 — 파일이 없으면 프롬프트 기준만으로 동작합니다.

---

## Hermes 스타일 메모리

### 사용자 메모리 (`memory/users/{user_id}.md`)

- 투자성향·금융이해도·관심 상품을 세션 간 파일로 저장
- `_before_agent_callback`에서 세션 최초 1회 로드, `_after_agent_callback`에서 저장
- `memory_consent = "declined"` 이면 저장 안 함
- eval 사용자 prefix 자동 감지해 테스트 데이터 저장 제외

### 에이전트 스킬 메모리 (`memory/agents/{agent_name}_skills.md`)

- 복잡한 케이스 해결 후 에이전트가 `append_skill` 자율 호출 → 패턴 누적
- investment_agent·pension_tax_agent: ADK 상태 플레이스홀더 `{agent_skills}` → 매 턴 동적 로드
- fraud_detection_agent: 모듈 로드 시 1회 정적 로드
- 항목 상한 20개 (초과 시 curator_app에 큐레이션 위임)
- 큐레이션 권고 기준: 10개 이상 누적

---

## 프로젝트 구조

```
barrier-free-agent/
├── app/
│   ├── agent.py                      오케스트레이터 barrier_free_financial_agent
│   ├── callbacks.py                  before/after 콜백 — 페르소나 감지·메모리 로드
│   ├── investment_agent.py           나비 — 투자·상품·ETF·거시경제
│   ├── pension_tax_agent.py          까치 — 퇴직연금·절세
│   ├── fraud_detection_agent.py      호야 — 보이스피싱·스미싱
│   ├── simulation_agent.py           토리 — 금융 계산 전용
│   ├── customer_management_agent.py  관리자 — 사용자 프로필 관리
│   ├── system_improvement_agent.py   관리자 — 스킬 문서 큐레이션
│   ├── skill_memory.py               Hermes 스킬 메모리 CRUD
│   ├── user_memory.py                크로스 세션 사용자 메모리
│   ├── navigation_tool.py            앱 화면 이동 맵
│   ├── literacy_tool.py              금융 용어 사전 검색
│   ├── guardrail_tool.py             금소법 투자권유 필터
│   ├── product_tool.py               예·적금·ISA·IRP 상품 조회 (FSS 공공데이터)
│   ├── krx_tool.py                   ETF 시세 (KRX API)
│   ├── macro_tool.py                 거시경제 지표 (ECOS API)
│   ├── fraud_tool.py                 보이스피싱 패턴 감지
│   └── simulation_tool.py            계산 도구 (세액공제·만기·연금)
│
├── ui/
│   └── demo.py                       Streamlit 데모
│
├── tests/
│   ├── unit/
│   │   ├── test_guardrail.py         금소법 가드레일 (5케이스)
│   │   ├── test_navigation.py        화면 이동 라우팅 (5케이스)
│   │   ├── test_literacy.py          금융 용어 검색 (5케이스)
│   │   ├── test_persona_routing.py   페르소나 감지·퓨샷 블록 (10케이스)
│   │   └── test_skill_memory.py      스킬 메모리 CRUD·상한 (8케이스)
│   ├── integration/
│   │   └── test_agent.py             에이전트 스트리밍 통합 테스트
│   └── eval/
│       ├── eval_config.json
│       └── evalsets/
│           ├── compliance.evalset.json
│           ├── fraud.evalset.json
│           ├── investment.evalset.json
│           └── pension_tax.evalset.json
│
├── data/
│   ├── knowledge/                    마크다운 지식베이스
│   │   ├── glossary/                 ETF, 금소법, 기준금리, 단리복리, 예금, 인플레이션
│   │   ├── investment/               ETF투자가이드, 예금적금비교, 채권, 투자성향, 펀드
│   │   ├── pension_tax/              IRP, ISA, 세액공제, 퇴직연금, 소비자권리
│   │   └── fraud/                    사기 유형 8종 + 예방수칙 + 피해시대처
│   ├── source/                       원본 공공데이터 및 수집 스크립트 (gitignore)
│   └── personas/                     페르소나 퓨샷 예시 (AI Hub 파생, gitignore — 로컬 전용)
│
├── memory/
│   ├── users/                        사용자별 프로필 파일
│   └── agents/                       에이전트별 스킬 누적 파일
│
├── scripts/
│   ├── build_persona_examples_aihub.py  AI Hub 은행상담 데이터 → 페르소나 퓨샷 생성
│   └── show_eval_results.py          eval 결과 뷰어
│
├── md/
│   ├── eval_log.md                   eval 실행 기록
│   ├── improvement_todo.md           개선 과제 목록
│   └── human_eval_checklist.md       수동 검토 체크리스트
│
├── .env                              API 키
└── pyproject.toml
```

---

## 시작하기

```bash
make install        # 의존성 설치
make playground     # ADK 웹 플레이그라운드
uv run streamlit run ui/demo.py  # Streamlit 데모
```

---

## 명령어

| 명령어 | 설명 |
|--------|------|
| `make install` | 의존성 설치 |
| `make playground` | ADK 웹 플레이그라운드 |
| `make eval` | 자동 평가 실행 (4개 evalset) |
| `make eval-all` | 전체 evalset 실행 |
| `make test` | 단위·통합 테스트 (35케이스) |
| `make lint` | 코드 품질 검사 |

---

## 평가 체계

### 자동 평가 (LLM-as-judge)

도메인별 evalset 4개, 총 42케이스.

| evalset | 도메인 |
|---------|--------|
| `compliance.evalset.json` | 금소법 준수 |
| `fraud.evalset.json` | 사기 탐지·경고 |
| `investment.evalset.json` | 투자·상품 상담 |
| `pension_tax.evalset.json` | 퇴직연금·절세 |

평가 기준: `rubric_based_final_response_quality_v1` (relevance / helpfulness / tone_compliance / no_product_recommendation), threshold 0.8

### Human Eval (`md/human_eval_checklist.md`)

LLM-as-judge가 놓치는 경계 케이스를 사람이 직접 검토합니다.

| 영역 | 항목 수 |
|------|--------|
| 준법성 (금소법·자본시장법) | 6개 |
| 정확성 (세율·한도·신고번호) | 6개 |
| 적합성 (투자성향·금융이해도 반영) | 4개 |
| 이해 가능성 (고령자 기준) | 5개 |
| 말투·형식 | 4개 |
| 사기 탐지 전용 | 5개 |

---

## 환경 변수

| 변수 | 설명 |
|------|------|
| `GOOGLE_API_KEY` | Gemini API 키 (필수) |
| `FSS_API_KEY` | 금융감독원 오픈API — 상품 조회 |
| `ECOS_API_KEY` | 한국은행 ECOS API — 거시경제 지표 |
| `KRX_API_KEY` | 한국거래소 API — ETF 시세 |
| `GOOGLE_GENAI_USE_VERTEXAI` | Vertex AI 사용 여부 (기본 false) |
