# barrier-free-agent

NH농협 올원뱅크 앱을 사용하는 디지털 금융 소외 계층을 위한 배리어프리 AI 안내원.
금융 용어 설명, 앱 화면 이동 안내, 상품 조회, 투자 가드레일을 제공합니다.

## 아키텍처

```
barrier_free_agent (오케스트레이터)
│
├── 직접 처리
│   ├── navigate_ui          # 앱 화면 이동 + 단계별 하이라이트 안내
│   ├── get_irp_info         # IRP 상품 정보 및 세액공제 안내
│   ├── get_isa_info         # ISA 상품 정보 및 유형 안내
│   └── set_user_profile     # 투자성향 세션 저장
│
└── financial_advisor_agent (서브에이전트)
    ├── explain_financial_term    # GraphRAG 기반 금융 용어 설명
    ├── check_investment_guardrail # 투자 권유 필터링 (금소법)
    ├── search_products / get_product_detail / compare_products  # FSS 예·적금 상품
    ├── get_etf_price / get_etf_prices_by_keyword  # KRX ETF 시세
    └── get_macro_indicators      # 한국은행 ECOS 거시경제 지표
```

## 프로젝트 구조

```
barrier-free-agent/
│
├── app/                        # 에이전트 백엔드
│   ├── agent.py                # 에이전트 정의 (barrier_free_agent + financial_advisor_agent)
│   ├── navigation_tool.py      # 화면 이동 + 하이라이트 안내
│   ├── literacy_tool.py        # GraphRAG 금융 용어 설명
│   ├── guardrail_tool.py       # 투자 권유 필터링
│   ├── product_tool.py         # FSS 예·적금·ISA·IRP 상품 조회
│   ├── krx_tool.py             # KRX ETF 시세
│   ├── macro_tool.py           # 한국은행 ECOS 거시경제 지표
│   ├── graph_rag_tool.py       # 지식 그래프 + 임베딩 파이프라인
│   └── terms_agent.py          # 약관 AI 분석 서브에이전트
│
├── ui/
│   └── demo.py                 # Streamlit 데모 (TTS/STT, 하이라이트, 동의 플로우)
│
├── tests/
│   ├── unit/                   # 도구 단위 테스트 (navigation, guardrail, literacy)
│   ├── integration/            # 에이전트 통합 테스트
│   └── eval/
│       ├── eval_config.json    # LLM-as-judge rubric 설정 (threshold 0.8)
│       └── evalsets/
│           └── basic.evalset.json  # 핵심 시나리오 18케이스
│
├── data/
│   ├── rag/                    # 금융 용어사전, FSS 상품 데이터, GraphRAG pkl
│   └── tos/                    # 약관 텍스트
│
├── scripts/
│   ├── build_graph.py          # 지식 그래프 빌드
│   └── build_embeddings.py     # 노드 임베딩 생성
│
├── md/                         # 프로젝트 문서
│   └── eval_log.md             # eval 실행 기록 및 설계 원칙
│
├── .env                        # API 키 (GOOGLE_API_KEY, FSS_API_KEY, ECOS_API_KEY 등)
└── pyproject.toml              # 의존성 관리
```

## 시작하기

```bash
# 의존성 설치
make install

# Streamlit 데모 실행
uv run streamlit run ui/demo.py

# ADK 플레이그라운드 (에이전트 직접 테스트)
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
| Run 1 | 2026-04-29 | 18/18 | baseline (safety net 있음) |
| Run 2 | 2026-04-29 | 17/18 | safety net 제거 |
| Run 3 | 2026-04-30 | 18/18 | 추천 표현 금지 + evalset 수정 + dotenv fix |

평가 기준: `rubric_based_final_response_quality_v1` (relevance / helpfulness / tone_compliance / no_product_recommendation), threshold 0.8
자세한 기록: [`md/eval_log.md`](md/eval_log.md)

## 환경 변수

| 변수 | 설명 |
|------|------|
| `GOOGLE_API_KEY` | Gemini API 키 |
| `FSS_API_KEY` | 금융감독원 오픈API |
| `ECOS_API_KEY` | 한국은행 ECOS API |
| `KRX_API_KEY` | 한국거래소 API |
| `GOOGLE_GENAI_USE_VERTEXAI` | Vertex AI 사용 여부 (기본 false) |
