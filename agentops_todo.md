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

## 🛠️ Phase 5. 고도화 및 운영 (Layer 4)

- [ ] **Observability 설정** (OpenTelemetry, Cloud Logging)
- [ ] **RAG 데이터 업데이트 자동화** (금융감독원 최신 용어 사전 반영)
- [ ] **사용자 피드백 기반 에이전트 성능 개선 (HITL)**

---

> **현재 상태**: Phase 2의 핵심 도구들(용어 풀이, 경로 안내, 가드레일) 구현 및 단위 테스트 완료. 이제 상품 정보 도구 개발 또는 에이전트 통합 단계로 진입 가능.
