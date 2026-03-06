# 배리어프리 금융 에이전트 — AgentOps To-Do List
> 스택: ADK · Python · Gemini CLI / Claude Code · Streamlit
> 타겟: 은행 앱 투자/자산관리 메뉴 × 노년층 · 주린이

---

## Phase 1. 기반 인프라 및 CI/CD 자동화

- [ ] **Agent Starter Pack으로 프로젝트 부트스트래핑**
  - Terraform 인프라 템플릿 생성
  - Cloud Build CI/CD 파이프라인 초기화
  - 평가 데이터셋 디렉토리 뼈대 생성 (`data/eval/`)

- [ ] **CI/CD 파이프라인 연동 확인**
  - 코드 변경 시 자동 빌드 트리거 설정
  - 도구(Tool) 변경 시 단위 테스트 자동 실행
  - 프롬프트 변경 시 정량적 평가 자동 실행

---

## Phase 2. 컴포넌트 레벨 평가 (Layer 1)

> 비(非) LLM 요소의 결정론적 검증 — 버그를 가장 앞단에서 차단

- [ ] **도구(Tool) 단위 테스트 작성** (`tests/unit/`)
  - `용어_설명_tool` (RAG 조회 — 금감원 금융용어사전)
  - `상품_조회_tool` (펀드·ETF·IRP 상품 정보 반환)
  - `위험도_계산_tool` (수익률·변동성 지표 계산)
  - `화면_네비게이션_tool` (노년층 UI 단계 가이드)
  - `guardrail_tool` (설명 vs 권유 경계 필터)

- [ ] **입력값 검증**
  - 정상 입력 / 잘못된 입력 / 엣지 케이스 시나리오별 통과 확인
  - 예: 존재하지 않는 금융 용어 쿼리 → 에러 핸들링 확인

- [ ] **API 및 데이터 처리 검증**
  - 외부 데이터 소스(금감원 등) 성공 / 에러 / 타임아웃 처리 확인
  - 벡터DB(RAG) 조회 실패 시 폴백(fallback) 동작 확인

---

## Phase 3. 궤적 평가 (Layer 2)

> 에이전트의 ReAct (Reason → Act → Observe) 추론 흐름 검증

- [ ] **절차적 정확성 검증**
  - 페르소나(노년층 / 주린이) 파악 → 올바른 에이전트로 분기되는지 확인
  - Orchestrator Agent의 목표 설정 및 가설 수립 로직 검토

- [ ] **도구 선택 및 매개변수 생성 검증**
  - "ETF가 뭐예요?" 질문 → `용어_설명_tool` 선택 여부 확인
  - "IRP 납입하러 왔어요" → `화면_네비게이션_tool` 선택 여부 확인
  - 각 Tool 호출 시 파라미터 추출·포맷팅 정확성 검증

- [ ] **골든 셋(Golden Set) 구축** (`tests/integration/`)

  | 시나리오 | 페르소나 | 예상 ReAct 궤적 |
  |---|---|---|
  | "ETF가 뭔가요?" | 주린이 | Reason: 용어 질문 → Act: 용어_설명_tool → Observe: 정의 반환 → 쉬운 말로 답변 |
  | "IRP 납입하러 왔어요" | 노년층 | Reason: 네비게이션 필요 → Act: 화면_네비게이션_tool → Observe: 단계 반환 → 단계별 안내 |
  | "이 펀드 사야 하나요?" | 주린이 | Reason: 권유 요청 감지 → Act: guardrail_tool → Observe: 경계 플래그 → 설명으로 전환 |
  | "수익률이 뭔지 모르겠어요" | 노년층 | Reason: 용어+네비게이션 복합 → Act: 용어_설명_tool → Observe: 정의 → 쉬운 말 + 화면 안내 |

---

## Phase 4. 결과 평가 (Layer 3)

> 최종 사용자에게 전달되는 답변 품질 평가

- [ ] **사실 기반성 및 정확성(Grounding) 확인**
  - 에이전트 답변이 RAG로 조회된 금감원 데이터 기반인지 검증
  - 환각(Hallucination) 여부: 존재하지 않는 상품명·수익률 생성 여부 점검

- [ ] **유용성 및 어조 점검**
  - 노년층: 경어체·단문·쉬운 단어 사용 여부
  - 주린이: 금융 용어 병기 + 풀어쓰기 형식 준수 여부
  - 투자 권유 표현 미포함 여부 (guardrail 통과 확인)

- [ ] **자동화 스코어링 적용**
  - Vertex AI Gen AI 평가 서비스(LLM-as-judge) 연동
  - 평가 기준 정의: 용어 설명 충실도 / 어조 적합성 / 정보 정확성
  - Human-in-the-loop(HITL) 피드백 수집 인터페이스 구성 (Streamlit 내 👍👎)

---

## Phase 5. 시스템 모니터링 및 보안 가드레일 (Layer 4 + Security)

- [ ] **실시간 성능 트래킹 지표 정의 및 수집**
  - Tool 실패율
  - 사용자 피드백 점수 (HITL)
  - 작업당 ReAct 사이클 수
  - End-to-end 응답 지연 시간 (Latency)

- [ ] **Observability 연동**
  - OpenTelemetry 설정
  - Cloud Trace / Cloud Logging 연동
  - BigQuery로 실행 로그 라우팅

- [ ] **입출력 가드레일 적용**
  - 프롬프트 인젝션 공격 탐지 로직
  - 출력물 유해 콘텐츠 필터링
  - **금융소비자보호법 준수**: "설명" vs "권유" 경계 필터 (`guardrail_tool`)

- [ ] **최소 권한 원칙(Least Privilege) 준수**
  - IAM 역할 최소화 (에이전트별 필요 리소스만 접근)
  - 서비스 계정 분리 (Orchestrator / Sub-agents / RAG DB)
  - 시크릿(API Key 등) Secret Manager 관리

---

## 부록. Streamlit 데모 체크리스트

- [ ] 사이드바: 페르소나 선택 (노년층 / 주린이) + 시나리오 선택
- [ ] 메인 영역: 모바일 앱 화면 목업 (이미지 또는 HTML 시뮬레이션)
- [ ] 에이전트 패널: ReAct 추론 과정 실시간 표시 + 최종 답변 출력
- [ ] 평가 패널: 응답 정확도 / 지연 시간 / 용어 설명 충실도 지표 시각화
- [ ] HITL 피드백: 답변별 👍 / 👎 수집 버튼

---

> **다음 단계**: Phase 1 부트스트래핑 완료 후, Phase 2 Tool 설계 및 단위 테스트 작성 착수
