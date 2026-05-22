# 보완 사항 TODO

## 1. RAG 전면 교체
- [ ] Semantic RAG + 명시적 관계 그래프 2중 구조로 재설계
  - Layer 1: 벡터 검색으로 관련 청크 검색 (Semantic RAG)
  - Layer 2: 인과 관계를 사람이 직접 정의한 Relational Graph 탐색
    - 예: 한국은행 -[금리인하]→ 채권가격상승 -[영향]→ IRP수익률변화
- [ ] 현재 임베딩 기반 노드 연결 방식 제거 (블랙박스 문제)
- [ ] 노드 간 엣지를 명시적 인과관계로 재정의

## 2. 약관 분석 기능 수정 (금소법) ✅ 완료 (2026-05-11)
- [x] AI가 약관을 요약·해석하는 기능 제거 → `terms_agent.py` 삭제, LLM 호출 제거
- [x] AI 형광펜(위험 조항 하이라이트)만 허용 → Python 패턴 매칭(`_fallback_highlight`)으로 전환
  - 허용: 위험 조항 위치를 색상으로 표시 (regex 고정 패턴, AI 개입 없음)
  - 금지: AI가 조항 내용을 요약하거나 해석하는 텍스트 생성
- [x] 기본 Suggest 칩 "IRP 약관 분석해줘" → "내 투자성향 진단해줘" 교체

## 3. 데이터 수집 보완
- [ ] FSS 실시간 API 연동 (현재 로컬 JSON 스냅샷)
- [ ] ETF 정보 자동 갱신 파이프라인 구축 (현재 수동 스크랩)
- [ ] 상품 커버리지 확대 (현재 IRP·ISA 위주)
- [ ] 약관 데이터 추가 수집 (현재 IRP 약관만 존재)
- [ ] 규정 데이터 최신화 주기 정의

## 4. get_ 상품 함수 하드코딩 제거 ✅ 완료 (2026-05-11)
- [x] `get_irp_info()`, `get_isa_info()`에 `investment_profile` 파라미터 추가
  - 위험회피형: 원금손실 경고 강조, 진단 우선 chip
  - 위험선호형: 진단 불필요, 포트폴리오/일임형 chip 우선
  - 미파악: 기존 기본 안내 유지
- [x] FSS 동적 API 전환은 보류 — FSS 등록 상품 수가 적어 실익 없음. 대신 로컬 JSON 데이터 확충
- [x] 키워드 → 특정 툴 고정 매핑 instruction 제거 → LLM 자율 판단으로 전환
- [x] 사용자 프로필 수집 방식 개선
  - 금융이해도: 대화 시작 시 칩(📗기초/📘일반/📕전문가) → ADK state 직접 write
  - 투자성향: 투자성향 진단 페이지(3문항 채점) → ADK state 직접 write
  - 에이전트 대화 중 파악 시 `set_user_profile` tool → ADK state 업데이트
  - dialog 열릴 때 ADK→`st.session_state["_ui_*"]` 동기화로 배지 즉시 반영

## 5. 답변 퀄리티 개선
- [ ] 고객 상황 반영 없이 동일 답변 나오는 케이스 식별 및 수정
- [ ] 멀티턴 문맥 활용도 향상 (이전 대화 참조 강화)
- [ ] 합쇼체·가드레일 외 엣지 케이스 evalset 추가 (현재 22케이스)

## 6. 서브에이전트 확장 및 프롬프트 다이어트

### 6-1. 절세 전문 에이전트 (`tax_saving_agent`)
- [ ] `app/tax_saving_agent.py` 생성
  - 모델: `gemini-3-flash-preview` (financial_advisor_agent와 동급)
  - 역할: 세액공제 시뮬레이션·절세 전략 안내 (투자 권유 아님, 세법 정보 제공)
- [ ] 전용 도구 구현: `calculate_tax_saving(income, irp_amount, isa_amount, pension_amount)`
  - 입력: 총급여(income), IRP 납입액, ISA 납입액, 연금저축 납입액
  - 출력: 예상 세액공제액, 환급 예상액, 연간 절세 효과
  - 근거: 조세특례제한법 기준 (IRP 900만 원 한도, 연금저축 600만 원 포함)
  - 소득구간별 공제율 분기: 총급여 5,500만 원 이하 16.5% / 초과 13.2%
- [ ] `barrier_free_agent` 위임 조건 추가
  - 트리거 키워드: "세액공제", "절세", "환급", "연말정산", "얼마나 돌려받"
  - 기존 `financial_advisor_agent` 위임 목록에서 분리
- [ ] `barrier_free_agent` 도구 목록에 `AgentTool(agent=tax_saving_agent)` 등록
- [ ] evalset에 절세 시뮬레이션 케이스 3개 이상 추가

### 6-2. 예적금 시뮬레이션 에이전트
- [ ] 예적금 시뮬레이션 에이전트 추가 (만기금액·이자 계산)

### 6-3. 프롬프트 다이어트
- [ ] 각 에이전트 instruction 프롬프트 다이어트
  - `barrier_free_agent`: 중복 규칙 정리, 위임 조건 단순화
  - `financial_advisor_agent`: 도구 사용 지침 축약
  - 에이전트별 역할 경계 명확히 재정의
