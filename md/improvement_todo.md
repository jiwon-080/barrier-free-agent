# 보완 사항 TODO

## 1. RAG → LLM Wiki + Hermes 메모리 구조로 전환

### 1-1. LLM Wiki 지식베이스 (Karpathy 패턴) ✅ 폴더 구조 완료 (2026-05-24)
- [x] `data/rag/` 레거시 전체 삭제 (GraphRAG pkl, JSON 사전, 스크랩 스냅샷)
- [x] 새 폴더 구조 생성
  ```
  data/
    source/documents/   ← 원본 PDF
    source/scripts/     ← 스크랩 스크립트
    knowledge/          ← Karpathy LLM Wiki (Obsidian 마크다운)
      schema.md         ← 네이밍·작성 규칙
      index.md          ← 전체 페이지 목록
      investment/       ← 나비 도메인
      pension_tax/      ← 까치 도메인
      fraud/            ← 호야 도메인
      glossary/         ← 공용 금융 용어
      wiki_admin/       ← 위키 건강 관리 (lint, log, skills)
  ```
- [x] `data/knowledge/` 각 도메인 마크다운 페이지 작성 ✅ 완료 (2026-05-26)
  - investment: 투자성향.md, 예금적금비교.md, ETF투자가이드.md, 펀드.md, 채권.md
  - pension_tax: IRP.md, ISA.md, 세액공제.md, 퇴직연금.md
  - fraud: 기관사칭형.md, 대출빙자형.md, 메신저피싱.md, 스미싱.md, 투자빙자형.md, 납치협박형.md, 피해시대처.md
  - glossary: ETF.md, 인플레이션.md, 단리복리.md, 기준금리.md, 예금.md
- [x] `explain_financial_term` 백엔드 교체 ✅ 완료 (2026-05-26)
  - 기존: GraphRAG BFS(416줄) → 신규: 파일명·프론트매터 검색(36줄)
  - 임베딩·벡터 DB 없음 — wiki md 파일 직접 검색 후 LLM context에 주입
- [x] `app/graph_rag_tool.py` 등 RAG 관련 app 코드 정리 ✅ 완료 (2026-05-26)

### 1-2. Hermes 스타일 메모리 구조
- [ ] `memory/agents/` — 에이전트별 스킬 문서
  - `investment_agent_skills.md`, `pension_tax_agent_skills.md` 등
  - 복잡한 케이스 해결 후 에이전트가 자동 append
- [ ] `memory/users/{user_id}.md` — 사용자 세션 메모리
  - 투자성향, 금융이해도, 관심 상품, 대화 핵심 요약 (대화 전문 미저장)
  - `_before_agent_callback`에서 해당 md 읽어 컨텍스트 주입
  - `_after_tool_callback`에서 세션 종료 시 자동 업데이트
- [ ] 사용자 동의 문구 UI 추가 (개인정보보호법)
  - "다음 방문 시 맞춤 안내를 위해 투자성향·금융이해도를 저장합니다"

### 1-3. 사용자 페르소나 few-shot (Nemotron-Personas-Korea)
- [ ] `nvidia/Nemotron-Personas-Korea` 데이터셋에서 age 55~80, 은퇴/주부/농업 직군 프로파일 10~20개 추출
- [ ] literacy_level별 대표 페르소나 few-shot 예시 작성
  - 기초 → 68세 은퇴 교사 페르소나 (말투·질문 패턴)
  - 일반 → 55세 중년 직장인
  - 전문가 → 금융업 종사자
- [ ] `_before_agent_callback`에서 literacy_level 기반 해당 few-shot 주입

---

## 2. 약관 분석 기능 수정 (금소법) ✅ 완료 (2026-05-11)
- [x] AI가 약관을 요약·해석하는 기능 제거 → `terms_agent.py` 삭제, LLM 호출 제거
- [x] AI 형광펜(위험 조항 하이라이트)만 허용 → Python 패턴 매칭(`_fallback_highlight`)으로 전환
- [x] 기본 Suggest 칩 "IRP 약관 분석해줘" → "내 투자성향 진단해줘" 교체

---

## 3. 데이터 수집 보완
- [ ] FSS 실시간 API 연동 (현재 로컬 JSON 스냅샷)
- [ ] ETF 정보 자동 갱신 파이프라인 구축 (현재 수동 스크랩)
- [ ] 상품 커버리지 확대 (현재 IRP·ISA 위주)
- [ ] 약관 데이터 추가 수집 (현재 IRP 약관만 존재)
- [ ] 규정 데이터 최신화 주기 정의

---

## 4. get_ 상품 함수 하드코딩 제거 ✅ 완료 (2026-05-11)
- [x] `get_irp_info()`, `get_isa_info()`에 `investment_profile` 파라미터 추가
- [x] FSS 동적 API 전환 보류 — 로컬 JSON 데이터 확충으로 대체
- [x] 키워드 → 특정 툴 고정 매핑 instruction 제거
- [x] 사용자 프로필 수집 방식 개선 (literacy chip + 투자성향 진단 페이지)

---

## 5. 답변 퀄리티 개선
- [ ] 고객 상황 반영 없이 동일 답변 나오는 케이스 식별 및 수정
- [ ] 멀티턴 문맥 활용도 향상 (이전 대화 참조 강화)
- [ ] evalset 추가 (현재 34케이스 — 목표 60+)

---

## 6. 에이전트 아키텍처 전면 개편 (Hermes 스타일)

### 6-0. 전체 구조

```
[사용자 대면]
barrier_free_agent (루트 — 라우팅·내비게이션·IRP/ISA 안내)
    ├── investment_agent       (투자·펀드·ETF·가드레일 전문)
    ├── pension_tax_agent      (퇴직연금·IRP·ISA·절세 전문)
    ├── simulation_agent       (계산 전담 피어 — 누구든 호출 가능)
    └── fraud_detection_agent  (보이스피싱·금융사기 탐지)

[백그라운드 — 사용자 비노출, 관리자 ADK 접근]
customer_management_agent    (고객 페르소나·메모리 DB·피드백 루프)
system_improvement_agent     (에이전트 스킬 문서 큐레이터)
```

**피어 위임 구조**: `simulation_agent`는 `AgentTool`로 감싸 여러 에이전트에 동시 등록.
`investment_agent`, `pension_tax_agent` 모두 계산이 필요할 때 `simulation_agent`를 호출.

### 6-1. financial_advisor_agent → investment_agent + pension_tax_agent 분리
- [ ] `app/investment_agent.py` 생성
  - 도구: `explain_financial_term`, `check_investment_guardrail`, `search_products`, `get_product_detail`, `compare_products`, `get_etf_price`, `get_etf_prices_by_keyword`, `get_macro_indicators`
  - 페르소나: 꼼꼼하고 객관적인 투자 정보 전문가
  - 스킬 메모리: `memory/agents/investment_agent_skills.md`
- [ ] `app/pension_tax_agent.py` 생성
  - 도구: `get_irp_info`, `get_isa_info`, `calculate_tax_saving`, `AgentTool(simulation_agent)`
  - 페르소나: 퇴직·절세 플래닝 전문가
  - 스킬 메모리: `memory/agents/pension_tax_agent_skills.md`
- [ ] `barrier_free_agent`에서 `financial_advisor_agent` 제거, 두 에이전트로 위임 분기 재설정

### 6-2. simulation_agent (신규 — 피어)
- [ ] `app/simulation_agent.py` 생성
  - 도구: `calculate_tax_saving`, `calculate_maturity_amount`, `calculate_pension_payout`
    - `calculate_tax_saving(income, irp_amount, isa_amount, pension_amount)` → 세액공제·환급액
    - `calculate_maturity_amount(principal, rate, months, product_type)` → 예적금 만기금액
    - `calculate_pension_payout(balance, start_age, duration_years)` → 연금 수령액 추정
  - 페르소나: 정확한 수치 계산 전담. 규정 해석 없음, 계산만.
  - 스킬 메모리: `memory/agents/simulation_agent_skills.md`
  - `AgentTool(simulation_agent)` → `investment_agent`, `pension_tax_agent` 양쪽에 등록

### 6-3. fraud_detection_agent (신규)
- [ ] `app/fraud_detection_agent.py` 생성
  - 도구: `check_fraud_pattern(text)` — 보이스피싱·금융사기 패턴 DB 기반 위험도 판정
  - 트리거: "이런 문자 받았는데", "전화가 왔는데", "이게 사기인가요"
  - 페르소나: 침착하고 명확한 보안 전문가
  - 출력: 위험도(높음/중간/낮음) + 신고 방법 안내

### 6-4. customer_management_agent (신규 — 백그라운드)
- [ ] `app/customer_management_agent.py` 생성
  - 역할: 대화 종료 후 `memory/users/{user_id}.md` 업데이트, 피드백 루프 관리
  - Nemotron 페르소나 프로파일 매칭 및 기록
  - 관리자가 ADK playground에서 "사용자 현황 보고해줘" 로 조회 가능
  - 별도 `admin_app = App(root_agent=customer_management_agent, name="admin")` 으로 분리

### 6-5. system_improvement_agent (신규 — 백그라운드)
- [ ] `app/system_improvement_agent.py` 생성
  - 역할: `memory/agents/` 하위 스킬 문서 주기적 정리·병합·삭제 (Hermes 스킬 큐레이터)
  - 7일 주기 또는 스킬 문서 10개 누적 시 실행
  - 관리자가 ADK playground에서 "스킬 업데이트 현황 보고해줘" 로 조회 가능

### 6-6. 에이전트 페르소나 추가 (전 에이전트)

> **BF Agent** — *Best Friend & Barrier Free*
> 금융 소외계층 누구에게나 든든한 친구가 되어주는 AI 금융 도우미.
> 각 에이전트는 동물 캐릭터 페르소나를 가지며, 친근하고 따뜻한 어조로 금융 정보를 전달합니다.

- [ ] 각 에이전트 instruction에 이름·성격·말투 가이드 블록 추가
  - `barrier_free_agent` → **"뭉치"** (둥글둥글 순한 백구)
    - 동네 백구처럼 친근하고 따뜻함. 어려운 금융 용어를 풀어서 차근차근, 어르신·초보자도 이해하기 쉽게 인내심 있게 설명.
  - `investment_agent` → **"나비"** (빠르고 영리한 고양이)
    - 눈치 빠르고 예리한 고양이처럼 시장 흐름을 짚어냄. 꼼꼼하고 객관적인 투자 정보를 군더더기 없이 세련된 어조로 전달.
  - `pension_tax_agent` → **"까치"** (좋은 소식을 물어오는 길조)
    - 퇴직금과 절세 혜택이라는 기쁜 소식을 날쌔게 물어오는 까치. 빈틈없고 신뢰감 있는 톤으로 절세 플랜을 정확히 짚어줌.
  - `simulation_agent` → **"토리"** (작지만 야무진 다람쥐)
    - 도토리를 야무지게 굴리는 다람쥐처럼 계산 전담. 수치와 시뮬레이션 결과를 군더더기 없이 간결하고 정확하게 툭 던져줌.
  - `fraud_detection_agent` → **"호야"** (든든하고 용맹한 호랑이)
    - 사기와 위협으로부터 자산을 지키는 호랑이. 침착하고 단호하며, 위험 감지 시 절도 있고 명확한 어조로 경고하고 대응 방법을 안내.

### 6-7. 프롬프트 다이어트
- [ ] `barrier_free_agent` instruction 중복 규칙 정리, 위임 조건 단순화
- [ ] 분리된 에이전트들의 instruction은 각자 역할에만 집중하도록 축약
