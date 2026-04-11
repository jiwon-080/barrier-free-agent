# 📋 배리어프리 금융 서비스 에이전트 AgentOps To-Do List

> 어르신 및 금융 초보자를 위한 초간편 금융 메뉴 탐색 및 안내 서비스

---

## ✅ Phase 1. 기초 인프라 및 분석 (완료)
- [x] **Agent Starter Pack 기반 프로젝트 구조 설정**
- [x] **NH농협 올원뱅크 UI 분석 및 이동 경로 데이터 확보**
- [x] **GEMINI.md 및 memory.md 가이드라인 작성**

---

## ✅ Phase 2. 핵심 도구(Tool) 개발 및 단위 검증 (완료)

- [x] **단위 테스트(Unit Test) 환경 구축** (pytest 완료)
- [x] **literacy_tool.py** (금융 용어 풀이 도구)
  - [x] RAG 기반 용어 사전 연동 로직
  - [x] `fss_glossary.json` > `krx_etf_info.json` 우선순위 기반 조회 (중복 시 FSS 우선)
  - [x] KRX ETF 통합: 위험등급 헤더 표시 기능 추가 — 2026-04-10
  - [x] `tests/unit/test_literacy.py` 검증 완료
- [x] **navigation_tool.py** (UI 경로 안내 도구)
  - [x] route 기반 반환값 구조로 전환 (`type`, `route`, `consent_message`, `voice_guide`)
  - [x] 실제 NH농협 앱 메뉴 기반으로 전면 수정 — 2026-04-08
    - ETF/펀드 고위험 차단 로직 제거 → `guardrail_tool` 위임
    - 실제 존재하는 메뉴만 등록 (예금/적금/펀드/ISA/퇴직연금/신탁/골드실버 등)
  - [x] `tests/unit/test_navigation.py` 검증 완료
- [x] **guardrail_tool.py** (금소법 준수 가드레일 도구)
  - [x] 투자 권유 및 과장 광고 키워드 필터링 로직
  - [x] `tests/unit/test_guardrail.py` 검증 완료
- [x] **krx_tool.py** (KRX ETF 실시간 시세 조회 도구) — 2026-04-10
  - [x] `get_etf_price(ticker_or_name)`: 단일 ETF 현재가·NAV·등락률 조회
  - [x] `get_etf_prices_by_keyword(keyword)`: 키워드 검색 후 최대 5개 반환
  - [x] FinanceDataReader 기반 (pykrx 세션 인증 문제로 우회)
- [x] **product_tool.py** (금융 상품 정보 조회 도구) — 2026-04-11
  - [x] FSS 상품 데이터(`fss_product.json`) 기반 예금/적금 조회·비교 로직
  - [x] `search_products` / `get_product_detail` / `compare_products` 구현
  - [ ] NH농협 공시 상품 수 부족 (예금 4개·적금 5개) → 추후 보완 예정

---

## ✅ Phase 2.5. RAG 데이터 수집 파이프라인 (진행 중)

- [x] **scrap_krx.py** 완료: FinanceDataReader → `data/rag/krx_etf_info.json` (1,088개 ETF) — 2026-04-10
- [x] **scrap_product.py** 개선 완료 — 2026-04-10
  - 저축은행(030300) 권역 추가
  - 폐지된 엔드포인트(annuity/ISA) 제거
- [x] **fss_product.json** 갱신: 예금/적금 (은행 + 저축은행) — 2026-04-10
- [x] **fss_bok_glossary.json** 구축 완료 — 2026-04-11
  - 한국은행 경제금융용어 700선 PDF 파싱 (`parse_bok_glossary.py`) → 684개
  - 금융감독원 파인 사전 병합 → 총 **1,191개** 용어
  - 파일명: `fss_glossary.json` → `fss_bok_glossary.json`으로 변경
- [x] **regulations.json** 작성 완료 — 2026-04-11
  - 연금계좌 세액공제 (600만/900만원 한도, 15%/12% 공제율) — 출처: 국세청
  - IRP 제도 기본 정보
- [ ] **scrap_product.py** 재실행 후 상품 수 확인 (저축은행 추가 효과 검증)

> **주의사항**
> - FSS annuity / ISA 엔드포인트는 FSS 폐지 → 404 반환, 사용 불가
> - IRP 상품 데이터는 FSS API 미제공 → `navigation_tool`로 화면 안내로 대체
> - KRX 직접 API / pykrx: 세션 인증 문제 → FinanceDataReader로 우회

---

## 🚀 Phase 3. 에이전트 통합 및 시나리오 테스트 (진행 중)

- [x] **에이전트 설정 (`app/agent.py`) 업데이트**
  - [x] 구현된 도구 등록: `guardrail_tool`, `literacy_tool`, `navigation_tool`
  - [x] `krx_tool`, `macro_tool`, `product_tool` 등록 완료 — 2026-04-11
  - [x] 합쇼체 말투 규칙 + 도구별 사용 지침 시스템 인스트럭션 보완 — 2026-04-11
  - [x] E2E 테스트 스크립트 (`scripts/test_agent_e2e.py`) 작성 및 검증 완료
- [ ] **통합 테스트(Integration Test) 시나리오 구성**
  - [ ] 용어 문의 → 경로 안내 → 가이드 제공으로 이어지는 시나리오 검증
  - [ ] 부적절한 요청에 대한 가드레일 작동 확인
- [ ] **Golden Set 구성 및 평가 (ADK Eval)**

---

## 🎨 Phase 4. UI/UX 데모 구현 (진행 중)

- [x] **Streamlit 기반 데모 웹 구현 (`ui/demo.py`) 기본 구조** — 2026-04-08
  - [x] `st.session_state["current_route"]` 기반 화면 라우팅
  - [x] NH올원뱅크 앱 mockup 화면 (모바일 너비 시뮬레이션)
  - [x] 에이전트 패널: 텍스트 입력 → `navigate_ui()` 직접 호출
  - [x] 동의 모달 → 확인 시 route 직접 이동 (4단계 → 1단계 단축)
  - [x] 라우트 맵: `home`, `financial_products`, `retirement_pension`, `irp_new`, `irp_tax_saving`, `my_pension`, `portfolio`, `investment_diagnosis`
- [ ] **`product_tool.py` 연동**: FSS 상품 데이터 기반 예금/적금 조회·비교 화면
- [ ] **에이전트 통합 테스트** (전체 시나리오 검증)
- [ ] **사용자 경험(UX) 고도화**
  - [ ] 시니어 대상 가시성(폰트 크기, 대비) 및 사용성 검토
  - [ ] `highlight_target` 시각 오버레이 활성화

---

## 🎙️ Phase 4.5. 음성 연동 (예정)

- [ ] **STT**: `st.audio_input` → Gemini API 전사
- [ ] **TTS**: gTTS + `st.audio` (한국어 품질 우수)

---

## 🕸️ Phase 5.5. GraphRAG 도입 (신규)

> **목표**: 현재 단순 키워드 매칭 기반인 `literacy_tool`을 금융 지식 그래프 기반 다중 홉(multi-hop) 추론으로 업그레이드.
> **기대 효과**: "IRP → 세액공제 → 한도 900만원 → irp_tax_saving 화면" 같은 연관 개념 연결 및 화면 경로 자동 추천.
> **기술 스택**: 로컬 데모 → `NetworkX` + Gemini Embeddings / 운영 확장 → Neo4j 또는 Memgraph

### 5.5-A. 그래프 스키마 설계 및 데이터 변환
- [ ] **노드(Node) 타입 정의**
  - `TermNode`: 금융 용어 (`IRP`, `ETF`, `세액공제` 등) — 기존 `fss_glossary.json` 변환
  - `ProductNode`: 금융 상품 (`개인형IRP`, `퇴직연금`, `예금` 등)
  - `RouteNode`: 앱 화면 경로 — `navigation_tool` 라우트 맵 변환
  - `RegNode`: 법/규정 조항 (금소법, 세액공제 한도 900만원 등)
  - `MacroNode`: 거시경제 지표 (금리/환율/물가) — 한국은행 ECOS API 실시간 조회
- [ ] **엣지(Edge) 타입 정의**
  - `RELATED_TO`: 용어 ↔ 용어
  - `SYNONYM_OF`: 동의어 (예: `ETF` ↔ `상장지수펀드`)
  - `LEADS_TO`: 용어/상품 → 화면 경로
  - `GOVERNED_BY`: 상품 → 규정
  - `AFFECTS`: 거시경제 지표 → 상품
  - `RISK_LEVEL`: 상품 → 위험도 레이블 (고위험 = guardrail 연동)
- [ ] **기존 데이터 변환 스크립트** (`scripts/build_graph.py`)
  - `fss_glossary.json` → `TermNode` 일괄 변환
  - `navigation_tool.py` 라우트 맵 → `RouteNode` + `LEADS_TO` 엣지 변환

### 5.5-B. GraphRAG 엔진 구현
- [ ] **`app/graph_rag_tool.py` 구현**
  - `build_graph()`: JSON/규칙 기반 데이터를 NetworkX 그래프로 로드
  - `graph_search(query: str) -> dict`: 쿼리에서 노드 탐색 후 다중 홉 결과 반환
  - `get_neighbors(node_id: str, depth: int = 2)`: n-hop 이웃 노드 조회
- [ ] **`literacy_tool.py` 통합**: 키워드 매칭 → `graph_search()` 결과 우선 사용, 없으면 기존 폴백

### 5.5-C. 에이전트 통합 및 검증
- [ ] **`agent.py`에 `graph_rag_tool` 등록**
- [ ] **통합 시나리오 검증 (multi-hop 3종)**
  - "IRP가 뭐야?" → `IRP(TermNode)` → `RELATED_TO` → `세액공제` → `LEADS_TO` → `irp_tax_saving`
  - "ETF 위험해?" → `ETF(TermNode)` → `RISK_LEVEL: HIGH` → `guardrail` 연동 → `investment_diagnosis`
  - "퇴직연금이랑 IRP 차이 뭐야?" → `퇴직연금` ↔ `IRP` 공통/차이 엣지 탐색
- [ ] **ADK Eval 골든셋에 multi-hop 케이스 추가** (`data/eval/golden_set_nh_bank.json`)

---

## 🛠️ Phase 6. 고도화 및 운영

- [ ] **Observability 설정** (OpenTelemetry, Cloud Logging)
- [ ] **RAG 데이터 업데이트 자동화** (금융감독원 최신 용어 사전 반영 → 그래프 자동 재빌드)
- [ ] **사용자 피드백 기반 에이전트 성능 개선 (HITL)**

---

> **현재 상태 (2026-04-11)**: Phase 2 전체 완료 (product_tool 포함). Phase 2.5 RAG 파이프라인 완료 (fss_bok_glossary 1,191개 + regulations.json). Phase 3 에이전트 통합 완료 (E2E 테스트 검증). 다음 단계: GraphRAG 구축 (build_graph.py → graph_rag_tool.py → literacy_tool 통합).
