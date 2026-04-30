# barrier-free-agent

디지털 금융 소외 계층을 위한 배리어프리 금융 에이전트 프레임워크.
금융 용어 설명, 앱 화면 이동 안내, 상품 조회, 투자 가드레일을 멀티에이전트 구조로 제공합니다.

> 구현 예시는 국내 모바일 뱅킹 앱을 기반으로 작성되었습니다.

## 아키텍처

```
[사용자 입력]
      │
      ▼
barrier_free_agent  (오케스트레이터 — app/agent.py)
│
├── navigate_ui          화면 이동 맵 + 하이라이트 안내 (navigation_tool.py)
├── get_irp_info         IRP 상품 정보·세액공제 안내   (product_tool.py)
├── get_isa_info         ISA 상품 정보·유형 안내       (product_tool.py)
├── set_user_profile     투자성향 세션 기록            (agent.py 인라인)
│
└── financial_advisor_agent  (서브에이전트 — AgentTool로 위임)
    ├── explain_financial_term     GraphRAG 기반 금융 용어 설명 (literacy_tool.py)
    ├── check_investment_guardrail 투자 권유 필터링 — 금소법    (guardrail_tool.py)
    ├── search_products            예·적금 상품 검색            (product_tool.py)
    ├── get_product_detail         상품 상세 조회               (product_tool.py)
    ├── compare_products           상품 비교                    (product_tool.py)
    ├── get_etf_price              ETF 시세·등락률              (krx_tool.py)
    ├── get_etf_prices_by_keyword  키워드 ETF 검색              (krx_tool.py)
    └── get_macro_indicators       기준금리·환율·물가           (macro_tool.py)

terms_analyzer_agent  (독립 실행 — app/terms_agent.py)
└── read_irp_terms       IRP 약관 전문 로드 후 위험 조항 하이라이팅
    (demo.py 약관 탭에서 별도 Runner로 직접 호출, barrier_free_agent와 비연결)
```

## 프로젝트 구조

```
barrier-free-agent/
│
├── app/
│   ├── agent.py            barrier_free_agent + financial_advisor_agent 정의
│   ├── terms_agent.py      terms_analyzer_agent 정의 (약관 분석 독립 에이전트)
│   ├── navigation_tool.py  화면 이동 맵 + 하이라이트
│   ├── literacy_tool.py    금융 용어 설명 (GraphRAG → 키워드 → 목업 폴백)
│   ├── guardrail_tool.py   금소법 키워드 필터
│   ├── product_tool.py     예·적금·ISA·IRP 상품 조회 (FSS 공공데이터)
│   ├── krx_tool.py         ETF 시세 (KRX API)
│   ├── macro_tool.py       거시경제 지표 (ECOS API)
│   └── graph_rag_tool.py   지식 그래프 BFS 탐색 엔진
│
├── ui/
│   └── demo.py             Streamlit 데모 (TTS/STT, 화면 시뮬레이션, 하이라이트)
│
├── tests/
│   ├── unit/               도구 단위 테스트
│   ├── integration/        에이전트 통합 테스트
│   └── eval/
│       ├── eval_config.json        rubric 설정 (threshold 0.8)
│       └── evalsets/
│           └── basic.evalset.json  핵심 시나리오 18케이스
│
├── data/
│   ├── rag/
│   │   ├── fss_bok_glossary.json   금융감독원·한국은행 용어사전
│   │   ├── fss_product.json        FSS 예·적금 상품 데이터
│   │   ├── krx_etf_info.json       KRX ETF 종목 정보
│   │   ├── knowledge_graph.pkl     빌드된 지식 그래프
│   │   └── node_embeddings.pkl     노드 임베딩 벡터
│   └── tos/
│       └── irp_terms.txt           IRP 상품설명서 (약관 분석용)
│
├── scripts/
│   ├── build_graph.py      지식 그래프 빌드 → knowledge_graph.pkl
│   └── build_embeddings.py 노드 임베딩 생성 → node_embeddings.pkl
│
├── md/
│   ├── eval_log.md         eval 실행 기록 및 설계 원칙
│   └── team_briefing.md    팀원 온보딩 문서
│
├── .env                    API 키
└── pyproject.toml          의존성 관리
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
| `make eval` | 평가 실행 (basic.evalset.json, 18케이스) |
| `make eval-all` | 전체 evalset 실행 |
| `make test` | 단위·통합 테스트 실행 |
| `make lint` | 코드 품질 검사 (ruff, ty, codespell) |

## 평가 현황

| Run | 날짜 | 결과 | 주요 변경 |
|-----|------|------|-----------|
| Run 1 | 2026-04-29 | 18/18 | baseline (UI safety net 있음) |
| Run 2 | 2026-04-29 | 17/18 | safety net 제거, LLM 자력 처리 검증 |
| Run 3 | 2026-04-30 | 18/18 | 추천 표현 금지 + evalset 멀티에이전트 반영 + dotenv fix |

평가 기준: `rubric_based_final_response_quality_v1` (relevance / helpfulness / tone_compliance / no_product_recommendation), threshold 0.8
자세한 기록: [`md/eval_log.md`](md/eval_log.md)

## 환경 변수

| 변수 | 설명 |
|------|------|
| `GOOGLE_API_KEY` | Gemini API 키 (필수) |
| `FSS_API_KEY` | 금융감독원 오픈API — 상품 조회 (없으면 로컬 데이터 사용) |
| `ECOS_API_KEY` | 한국은행 ECOS API — 거시경제 지표 |
| `KRX_API_KEY` | 한국거래소 API — ETF 시세 |
| `GOOGLE_GENAI_USE_VERTEXAI` | Vertex AI 사용 여부 (기본 false) |
