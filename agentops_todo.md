# 📋 배리어프리 금융 서비스 에이전트 AgentOps To-Do List

> 어르신 및 금융 초보자를 위한 초간편 금융 메뉴 탐색 및 안내 서비스

---

## ✅ Phase 1. 기초 인프라 및 분석 (완료)
- [x] **Agent Starter Pack 기반 프로젝트 구조 설정**
- [x] **NH농협 올원뱅크 UI 분석 및 이동 경로 데이터 확보**
- [x] **GEMINI.md 및 memory.md 가이드라인 작성**

---

## 🚀 Phase 2. 핵심 도구(Tool) 개발 및 단위 검증 (진행 중)

- [x] **단위 테스트(Unit Test) 환경 구축** (pytest 완료)
- [x] **literacy_tool.py** (금융 용어 풀이 도구)
  - [x] RAG 기반 용어 사전 연동 로직
  - [x] `tests/unit/test_literacy.py` 검증 완료
- [x] **navigation_tool.py** (UI 경로 안내 도구)
  - [x] 단계별 시각적/음성 가이드 응답 구조 설계
  - [x] `tests/unit/test_navigation.py` 검증 완료
- [x] **guardrail_tool.py** (금소법 준수 가드레일 도구)
  - [x] 투자 권유 및 과장 광고 키워드 필터링 로직
  - [x] `tests/unit/test_guardrail.py` 검증 완료
- [ ] **product_tool.py** (금융 상품 정보 조회 도구)
  - [ ] 상품 데이터(예적금, IRP) 연동 로직
  - [ ] 비교 분석 및 상세 설명 기능

---

## ✅ Phase 3. 에이전트 통합 및 시나리오 테스트 (Layer 2)

- [x] **에이전트 설정 (`app/agent.py`) 업데이트**
  - [x] 구현된 모든 도구(Tool) 등록: guardrail, literacy, navigation
  - [x] 시니어 특화 시스템 인스트럭션(Instruction) 보완 및 규칙 설정
- [ ] **통합 테스트(Integration Test) 시나리오 구성**
  - [ ] 용어 문의 -> 경로 안내 -> 가이드 제공으로 이어지는 시나리오 검증
  - [ ] 부적절한 요청에 대한 가드레일 작동 확인
- [ ] **Golden Set 구성 및 평가 (ADK Eval)**

---

## 🎨 Phase 4. UI/UX 및 배포 (Layer 3)

- [ ] **Streamlit 기반 데모 웹 구현 (`ui/demo.py`)**
  - [ ] 에이전트 응답에 따른 시각적 안내(Visual Instructions) 출력
  - [ ] 텍스트 및 음성 가이드 인터페이스
- [ ] **사용자 경험(UX) 고도화**
  - [ ] 시니어 대상 가시성(폰트 크기, 대비) 및 사용성 검토

---

## 🕸️ Phase 5.5. GraphRAG 도입 (신규)

> **목표**: 현재 단순 키워드 매칭 기반인 `literacy_tool`을 금융 지식 그래프 기반 다중 홉(multi-hop) 추론으로 업그레이드.
> **기대 효과**: "IRP → 세액공제 → 한도 900만원 → irp_tax_saving 화면" 같은 연관 개념 연결 및 화면 경로 자동 추천.

### 데이터 수집
- [ ] 금융감독원 API를 이용해, 고도화된 수집

### 5.5-A. 그래프 스키마 설계 및 데이터 변환
- [ ] **노드(Node) 타입 정의**
  - `TermNode`: 금융 용어 (`IRP`, `ETF`, `세액공제` 등) — 기존 `fss_glossary.json` 변환
  - `ProductNode`: 금융 상품 (`개인형IRP`, `퇴직연금`, `예금` 등)
  - `RouteNode`: 앱 화면 경로 (`irp_tax_saving`, `retirement_pension` 등) — `navigation_tool` 라우트 맵 변환
  - `RegNode`: 법/규정 조항 (금소법, 세법 세액공제 한도 등)
- [ ] **엣지(Edge) 타입 정의**
  - `RELATED_TO`: 용어 ↔ 용어 (예: `IRP` ↔ `퇴직연금`)
  - `SYNONYM_OF`: 동의어 (예: `ETF` ↔ `상장지수펀드`)
  - `LEADS_TO`: 용어/상품 → 화면 경로 (예: `IRP세액공제` → `irp_tax_saving`)
  - `GOVERNED_BY`: 상품 → 규정 (예: `개인형IRP` → `연금계좌세액공제_900만원`)
  - `RISK_LEVEL`: 상품 → 위험도 레이블 (고위험 = guardrail 연동)
- [ ] **기존 데이터 변환 스크립트** (`scripts/build_graph.py`)
  - `fss_glossary.json` → `TermNode` 일괄 변환
  - `navigation_tool.py` 라우트 맵 → `RouteNode` + `LEADS_TO` 엣지 변환

### 5.5-B. GraphRAG 엔진 구현
- [ ] **라이브러리 선택 및 설치**
  - 데모용(로컬, 외부 서비스 불필요): `NetworkX` + `sentence-transformers` (또는 Gemini Embeddings)
  - 운영 확장 시: `Neo4j` 또는 `Memgraph`
- [ ] **`app/graph_rag_tool.py` 구현**
  - `build_graph()`: JSON/규칙 기반 데이터를 NetworkX 그래프로 로드
  - `graph_search(query: str) -> dict`: 쿼리에서 노드 탐색 후 다중 홉 결과 반환
    - 반환 구조: `{"matched_term": ..., "related_terms": [...], "suggested_route": ..., "regulation_hint": ...}`
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

## 🛠️ Phase 6. 고도화 및 운영 (Layer 4)

- [ ] **Observability 설정** (OpenTelemetry, Cloud Logging)
- [ ] **RAG 데이터 업데이트 자동화** (금융감독원 최신 용어 사전 반영 → 그래프 자동 재빌드)
- [ ] **사용자 피드백 기반 에이전트 성능 개선 (HITL)**

---

> **현재 상태**: Phase 2의 핵심 도구들(용어 풀이, 경로 안내, 가드레일) 구현 및 단위 테스트 완료. Phase 5.5 GraphRAG 도입 계획 수립됨 (2026-04-03). 다음 단계: `product_tool.py` 완성 또는 GraphRAG 스키마 설계 착수.
