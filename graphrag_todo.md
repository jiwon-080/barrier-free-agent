# GraphRAG 사전 구축 To-Do List

> 배리어프리 에이전트 금융 지식 그래프 구축 체크리스트
> 참고: `graphrag_guide.md` (상세 가이드 및 전체 코드)

---

## Phase A. 데이터 수집

### A-1. 기존 데이터 점검 및 보강
- [ ] `data/rag/fss_glossary.json` 구조 점검
  - [ ] 전체 항목 수 확인 (현재 몇 개인지 파악)
  - [ ] `related_terms` 필드 유무 확인 → 없으면 수동/크롤링으로 추가 필요
  - [ ] `aliases`(동의어) 필드 없는 항목 식별 (ETF↔상장지수펀드, IRP↔개인형퇴직연금계좌 등)
- [ ] IRP·퇴직연금 관련 핵심 용어 누락 여부 점검
  - 필수: `IRP`, `DC형`, `DB형`, `세액공제`, `연금저축계좌`, `디폴트옵션`, `ETF`, `펀드`, `퇴직급여`

### A-2. 금융감독원 파인 크롤링 (확장)
- [ ] `robots.txt` 확인 및 크롤링 허용 범위 파악
- [ ] `scripts/crawl_fss_glossary.py` 작성
  - [ ] 목록 페이지 파싱 (페이지네이션 처리)
  - [ ] 상세 페이지에서 `related_terms` 파싱
  - [ ] 요청 간격 1.5초 이상 설정
- [ ] 크롤링 실행 → `data/rag/fss_glossary_full.json` 저장
- [ ] 기존 `fss_glossary.json`과 병합 (중복 제거, 파일 데이터 우선)

### A-3. NH농협 상품 데이터 정리
- [ ] `data/nh_products.json` 수동 작성 (가이드 내 샘플 참고)
  - [ ] 개인형IRP 세액공제용
  - [ ] 개인형IRP 퇴직금수령용
  - [ ] 확정기여형(DC) 퇴직연금
  - [ ] 각 상품의 `risk_level`, `eligible`, `related_terms`, `route` 필드 채우기

### A-4. 세법·규정 데이터 정리
- [ ] `data/regulations.json` 수동 작성 (가이드 내 샘플 참고)
  - [ ] IRP 세액공제 한도 (연 900만원, 세율 16.5%/13.2%)
  - [ ] 연금저축 세액공제 한도 (연 600만원)
  - [ ] 금소법 투자권유 규정 (guardrail 연동)
  - [ ] 퇴직급여보장법 IRP 의무 이전 규정

---

## Phase B. 그래프 스키마 확정

- [ ] 노드 타입 4종 필드 정의 확정 (`TermNode`, `ProductNode`, `RouteNode`, `RegNode`)
- [ ] 엣지 타입 6종 방향 및 의미 확정
  - `RELATED_TO`, `SYNONYM_OF`, `LEADS_TO`, `HAS_PRODUCT`, `GOVERNED_BY`, `TRIGGERS_GUARDRAIL`
- [ ] `navigation_tool.py`의 전체 라우트 목록 → `RouteNode` 매핑 표 작성
  - 현재 라우트: `home`, `financial_products`, `retirement_pension`, `irp_new`, `irp_tax_saving`, `my_pension`, `portfolio`, `investment_diagnosis`
- [ ] 고위험 트리거 용어 목록 확정 (ETF, 펀드, FUND → `TRIGGERS_GUARDRAIL`)

---

## Phase C. 그래프 구축 스크립트

- [ ] `uv add networkx` 실행 후 `pyproject.toml` 확인
- [ ] `scripts/build_graph.py` 작성 (가이드 섹션 3-2 참고)
  - [ ] `fss_glossary_full.json` → `TermNode` 일괄 변환
  - [ ] `nh_products.json` → `ProductNode` + `LEADS_TO`/`HAS_PRODUCT` 엣지
  - [ ] `regulations.json` → `RegNode` + `GOVERNED_BY` 엣지
  - [ ] `navigation_tool.py` 라우트 맵 → `RouteNode` + `LEADS_TO` 엣지
  - [ ] 고위험 용어 → `TRIGGERS_GUARDRAIL` 엣지
  - [ ] 결과를 `data/rag/knowledge_graph.pkl`로 저장
- [ ] `uv run python scripts/build_graph.py` 실행 성공 확인
  - 기대 출력: `그래프 구축 완료: XXX 노드, YYY 엣지`

---

## Phase D. 검색 엔진 구현

### D-1. 기본 탐색 (임베딩 없이)
- [ ] `app/graph_rag_tool.py` 작성
  - [ ] `load_graph()`: pkl 로드
  - [ ] `_find_start_node(query, G)`: 정확 일치 → 부분 매칭
  - [ ] `graph_search(query, depth=2)`: BFS 다중 홉 탐색
  - [ ] 반환 구조: `matched_term`, `definition`, `related_terms`, `suggested_route`, `regulation_hint`, `guardrail`, `products`

### D-2. 임베딩 인덱스 (선택적 고도화)
- [ ] Gemini Embeddings API (`models/text-embedding-004`) 연동 확인
  - 대안: `sentence-transformers` 로컬 모델 (`uv add sentence-transformers`)
- [ ] `build_embedding_index(G)` 구현 → `data/rag/node_embeddings.pkl` 저장
- [ ] `find_node_by_query(query, index, G, top_k=3)` 구현 (코사인 유사도)
- [ ] `_find_start_node`에 임베딩 폴백 연결

---

## Phase E. 에이전트 통합

- [ ] `literacy_tool.py` 수정
  - [ ] `from app.graph_rag_tool import graph_search` 추가
  - [ ] GraphRAG 결과 우선 사용 → 없으면 기존 키워드 검색 폴백
  - [ ] `regulation_hint` 있으면 응답에 세액공제 한도 등 자동 포함
- [ ] `agent.py`에 `graph_rag_tool` 등록 여부 검토
  - `graph_search`를 literacy_tool 내부에서만 쓸 경우 별도 등록 불필요
  - 에이전트가 직접 그래프 탐색해야 할 경우 별도 tool로 등록
- [ ] `navigation_tool.py`와 연동 검토
  - `graph_search`의 `suggested_route` → `navigate_ui(route)` 자동 호출 여부 결정

---

## Phase F. 검증

### F-1. 그래프 구조 검증
- [ ] `scripts/validate_graph.py` 작성 및 실행
  - [ ] 노드·엣지 수 확인
  - [ ] 고립 노드 0개 목표
  - [ ] 필수 노드 존재 확인 (`term_IRP`, `term_ETF`, `route_irp_tax_saving` 등)

### F-2. 시나리오 탐색 검증 (핵심 5종)
- [ ] `"IRP"` → `suggested_route: irp_tax_saving`, `guardrail: False`
- [ ] `"ETF"` → `suggested_route: investment_diagnosis`, `guardrail: True`
- [ ] `"세액공제"` → `regulation_hint` 포함 (900만원 한도)
- [ ] `"퇴직연금"` → `related_terms`에 IRP, DC 포함
- [ ] `"아무말대잔치"` → `matched_term: None` (폴백 정상 동작)

### F-3. ADK Eval 골든셋 확장
- [ ] `data/eval/golden_set_nh_bank.json`에 multi-hop 시나리오 추가
  - [ ] "IRP가 뭐야? 어디서 가입해?" → 용어 설명 + 화면 이동 통합 응답
  - [ ] "ETF 위험해?" → 가드레일 동작 + 투자성향진단 안내
  - [ ] "퇴직연금이랑 IRP 차이 뭐야?" → 두 노드 비교 응답
- [ ] `make eval` 실행 → multi-hop 케이스 통과율 측정

---

## 완료 기준 (Definition of Done)

| 항목 | 기준 |
|---|---|
| 그래프 크기 | TermNode 100개 이상, RouteNode 전체 라우트 커버 |
| 탐색 성공률 | 핵심 5종 시나리오 100% 통과 |
| 가드레일 연동 | ETF/펀드 쿼리 시 `guardrail: True` + `investment_diagnosis` 반환 |
| literacy_tool 통합 | GraphRAG 결과 우선 사용, 폴백 정상 동작 |
| ADK Eval | multi-hop 케이스 골든셋 추가 및 통과 |
