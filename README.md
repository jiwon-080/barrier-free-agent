# barrier-free-agent

디지털 금융 소외 계층을 위한 배리어프리 금융 에이전트 프레임워크.  
고령층·사회초년생·주부 등 페르소나를 자동 감지해 맞춤형 금융 상담, 앱 화면 이동, 절세 플래닝을 멀티에이전트 구조로 제공합니다.

> 구현 예시는 국내 모바일 뱅킹 앱을 기반으로 작성되었습니다.

## 아키텍처

```
[사용자 입력]
      │
      ▼
_before_agent_callback  (callbacks.py)
  ① 사용자 메모리 로드 (세션 최초 1회)
  ② 페르소나 자동 감지 — LLM 퓨샷 분류 → user:persona 상태 주입
  ③ 에이전트 스킬 메모리 동적 로드 → agent_skills 상태 주입
  ④ user_profile_summary 구성 (페르소나 힌트 + 투자성향 + 금융이해도)
      │
      ▼
barrier_free_agent  (오케스트레이터 — app/agent.py)
│
├── navigate_ui               화면 이동 맵 + 하이라이트 안내    (navigation_tool.py)
├── set_user_profile          투자성향·금융이해도 세션 기록      (agent.py 인라인)
│
├── investment_agent  (서브에이전트 — '나비')
│   ├── explain_financial_term      금융 용어 사전 검색           (literacy_tool.py)
│   ├── check_investment_guardrail  투자 권유 필터 — 금소법       (guardrail_tool.py)
│   ├── search_products / get_product_detail / compare_products   (product_tool.py)
│   ├── get_etf_price / get_etf_prices_by_keyword                 (krx_tool.py)
│   ├── get_macro_indicators        기준금리·환율·물가            (macro_tool.py)
│   ├── simulation_agent            금융 시뮬레이션 계산 위임
│   └── append_skill                Hermes 스킬 메모리 누적
│
├── pension_tax_agent  (서브에이전트 — '까치')
│   ├── get_irp_info / get_isa_info  IRP·ISA 상품 정보·세액공제  (product_tool.py)
│   ├── simulation_agent             세액공제 환급액·연금 시뮬레이션 위임
│   └── append_skill                 Hermes 스킬 메모리 누적
│
├── fraud_detection_agent  (서브에이전트 — '망치')
│   └── detect_fraud_pattern         보이스피싱·스미싱 패턴 감지  (fraud_tool.py)
│
├── customer_management_agent  (서브에이전트)
│   └── 고객 정보 조회·관리
│
└── system_improvement_agent  (서브에이전트 — Hermes 큐레이터)
    └── Hermes 스킬 문서 정리·통합·우선순위 조정
```

## 페르소나 라우팅

첫 번째 사용자 발화에서 LLM이 퓨샷 예시(30개)를 참고해 페르소나를 자동 분류합니다.

| 페르소나 | 말투·특징 | 안내 조정 |
|---------|----------|---------|
| 고령층 | 60대+, 구어체, 연금·손주 언급 | 쉬운 단어, 큰글 모드 안내 |
| 사회초년생 | 20대, 알바·주린이·청년 상품 | 기초 개념, 청년 전용 상품 우선 |
| 주부 | 가계 담당, 배우자·자녀 중심 | 가계 관점, 배우자 공제 안내 |
| 직장인 | 연말정산·4대보험·퇴직금 언급 | 근로소득 절세 중심 |
| 중장년 | 40~50대, 노후 준비 시작 | 은퇴까지 기간 고려 플랜 |

퓨샷 데이터: `data/personas/few_shot_examples.json` (고령층 10개, 나머지 각 5개)  
수집 스크립트: `scripts/collect_persona_utterances.py --persona 고령층 | --all`

## 스킬 메모리 (Hermes 패턴)

에이전트가 복잡한 케이스(도구 2개 이상 순차 사용)를 해결하면 `append_skill` 도구로 패턴을 `memory/agents/{agent_name}_skills.md`에 자동 누적합니다.  
다음 대화 시 `_before_agent_callback`이 해당 파일을 동적으로 읽어 `agent_skills` 상태로 주입합니다.

- 항목 상한: 20개 (초과 시 `system_improvement_agent`에 큐레이션 위임)
- 관리: `make skill-list` 또는 `system_improvement_agent` 직접 호출

## 프로젝트 구조

```
barrier-free-agent/
│
├── app/
│   ├── agent.py                   barrier_free_agent 오케스트레이터
│   ├── callbacks.py               before/after 콜백 — 페르소나 라우팅·스킬 로드
│   ├── skill_memory.py            Hermes 스킬 메모리 CRUD
│   ├── user_memory.py             사용자 메모리 영속성
│   ├── investment_agent.py        나비 — 투자·상품 전문
│   ├── pension_tax_agent.py       까치 — 퇴직연금·절세 전문
│   ├── fraud_detection_agent.py   망치 — 보이스피싱 감지
│   ├── customer_management_agent.py
│   ├── system_improvement_agent.py  Hermes 큐레이터
│   ├── simulation_agent.py        금융 시뮬레이션 계산기
│   ├── navigation_tool.py         앱 화면 이동 맵
│   ├── literacy_tool.py           금융 용어 사전 검색
│   ├── guardrail_tool.py          금소법 키워드 필터
│   ├── product_tool.py            예·적금·ISA·IRP 상품 조회 (FSS 공공데이터)
│   ├── krx_tool.py                ETF 시세 (KRX API)
│   ├── macro_tool.py              거시경제 지표 (ECOS API)
│   ├── fraud_tool.py              보이스피싱 패턴 감지
│   └── simulation_tool.py         시뮬레이션 계산 도구
│
├── ui/
│   └── demo.py                    Streamlit 데모 (TTS/STT, 화면 시뮬레이션)
│
├── tests/
│   ├── unit/
│   │   ├── test_guardrail.py      금소법 가드레일 키워드 감지 (5케이스)
│   │   ├── test_navigation.py     화면 이동 라우팅 (5케이스)
│   │   ├── test_literacy.py       금융 용어 검색 (5케이스)
│   │   ├── test_persona_routing.py  페르소나 감지·퓨샷 블록 (12케이스)
│   │   └── test_skill_memory.py   스킬 메모리 CRUD·상한 (8케이스)
│   ├── integration/
│   │   └── test_agent.py          에이전트 스트리밍 통합 테스트
│   └── eval/
│       ├── eval_config.json       rubric 설정 (threshold 0.8)
│       └── evalsets/
│           └── basic.evalset.json 핵심 시나리오 42케이스
│
├── data/
│   ├── knowledge/                 LLM Wiki (Karpathy 패턴 — 임베딩 없음)
│   │   ├── glossary/              금융 용어 사전 (ETF, 기준금리, 예금 등)
│   │   ├── investment/            투자 가이드 (ETF, 채권, 펀드, 투자성향)
│   │   ├── pension_tax/           퇴직연금·절세 (IRP, ISA, 세액공제, 금소법)
│   │   └── fraud/                 보이스피싱 유형·예방수칙
│   ├── personas/
│   │   └── few_shot_examples.json 페르소나 퓨샷 예시 30개
│   └── source/                    원본 공공데이터 (FSS, KRX 등)
│
├── memory/
│   └── agents/                    Hermes 스킬 문서 (에이전트별 자동 누적)
│
├── scripts/
│   └── collect_persona_utterances.py  퓨샷 예시 수집 파이프라인 (재현 가능)
│
├── .env                           API 키
└── pyproject.toml                 의존성 관리
```

## 시작하기

```bash
# 의존성 설치
make install

# Streamlit 데모 실행
uv run streamlit run ui/demo.py

# ADK 플레이그라운드 (도구 호출 흐름 디버깅)
make playground
```

## 명령어

| 명령어 | 설명 |
|--------|------|
| `make install` | 의존성 설치 |
| `make playground` | ADK 웹 플레이그라운드 실행 |
| `make eval` | 평가 실행 (basic.evalset.json, 42케이스) |
| `make eval-all` | 전체 evalset 실행 |
| `make test` | 단위·통합 테스트 실행 (35케이스) |
| `make lint` | 코드 품질 검사 (ruff, ty, codespell) |

## 평가 현황

| Run | 날짜 | 결과 | 주요 변경 |
|-----|------|------|-----------|
| Run 1 | 2026-04-29 | 18/18 | baseline |
| Run 2 | 2026-04-29 | 17/18 | safety net 제거 |
| Run 3 | 2026-04-30 | 18/18 | 추천 표현 금지 + evalset 멀티에이전트 반영 |
| Run 4 | 2026-05-xx | 42/42 | MAS 전환 — 에이전트 분리·사용자 메모리 콜백 |

평가 기준: `rubric_based_final_response_quality_v1` (relevance / helpfulness / tone_compliance / no_product_recommendation), threshold 0.8

## 환경 변수

| 변수 | 설명 |
|------|------|
| `GOOGLE_API_KEY` | Gemini API 키 (필수) |
| `FSS_API_KEY` | 금융감독원 오픈API — 상품 조회 (없으면 로컬 데이터 사용) |
| `ECOS_API_KEY` | 한국은행 ECOS API — 거시경제 지표 |
| `KRX_API_KEY` | 한국거래소 API — ETF 시세 |
| `GOOGLE_GENAI_USE_VERTEXAI` | Vertex AI 사용 여부 (기본 false) |
