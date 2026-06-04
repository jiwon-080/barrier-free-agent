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

### 1-2. Hermes 스타일 메모리 구조 (2026-05-31 부분 완료)
- [ ] `memory/agents/` — 에이전트별 스킬 문서
  - `investment_agent_skills.md`, `pension_tax_agent_skills.md` 등
  - 복잡한 케이스 해결 후 에이전트가 자동 append
- [x] `memory/users/{user_id}.md` — 사용자 세션 메모리 ✅ (2026-05-31)
  - 투자성향, 금융이해도, 관심 상품 저장 (YAML 프론트매터)
  - `_before_agent_callback`에서 파일 로드 → 세션 state 주입
  - `_after_agent_callback`에서 세션 종료 시 자동 저장
  - eval 사용자 prefix(`nav_user_`, `pt_user_` 등) 자동 스킵
- [x] 사용자 동의 문구 UI 추가 (개인정보보호법) ✅
  - `ui/demo.py`: 최초 방문 시 동의 배너, 💾/👤 뱃지, 기억 초기화 버튼 구현
  - 백엔드: `user:memory_consent` declined 시 저장 스킵

### 1-3. 페르소나별 실제 발화 데이터셋 + few-shot 라우팅 레이어 (현직자 조언 반영)

> ❌ Nemotron-Personas-Korea 폐기 — 합성 데이터로 실제 금융 발화와 무관. 실제 소스에서 수집.

**수집 경로**
- 네이버 지식인 금융 카테고리 (IRP, ISA, 연금, 예금 검색 결과)
- 네이버 카페 (노후준비, 주부재테크, 시니어재테크)
- 유튜브 댓글 — 금융사 공식 채널 고령자 시청 비율 높은 영상
- 금융감독원 금융소비자포털 상담 사례 공개분

**페르소나 타입 및 발화 특징**
- 노년층: "이거 어떻게 하는건가요", "제가 잘 몰라서요", "은행가면 되나요"
- 주부층: "남편 월급에서", "애들 학원비 빼고", "노후에 얼마나 받을수있나요"
- 직장인: "연말정산 때", "한도 다 채우려면", "DC형이랑 DB형 차이가"

**구현**
- [ ] 페르소나별 실제 발화 20~30개씩 수집 및 정제
- [ ] 수집된 발화 기반 few-shot 예시 작성 (`data/personas/` 또는 instruction 직접 삽입)
- [ ] `_before_agent_callback` 앞단에 few-shot 라우팅 레이어 추가
  - 발화 패턴 → persona_type 판단 → 응답 스타일 가이드 주입

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
- [ ] evalset 추가 (현재 42케이스 — 회귀 버그 또는 미커버 시나리오 발견 시 추가)
- [x] **human eval 셋 구성** ✅ (2026-05-31)
  - `md/human_eval_checklist.md` 작성 완료
  - 준법성(C1~C6), 정확성(A1~A6), 적합성(S1~S4), 이해가능성(U1~U5), 말투(T1~T4), 사기탐지(F1~F5)
  - 우선 검토 케이스 6개 카테고리 지정

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

### 6-1. financial_advisor_agent → investment_agent + pension_tax_agent 분리 ✅ 완료 (2026-05-31)
- [x] `app/investment_agent.py` 별도 파일 분리
  - 스킬 메모리: `memory/agents/investment_agent_skills.md`
- [x] `app/pension_tax_agent.py` 별도 파일 분리
  - 스킬 메모리: `memory/agents/pension_tax_agent_skills.md`
- [x] `barrier_free_agent`에서 `financial_advisor_agent` 제거, 두 에이전트로 위임 분기 재설정 ✅
- [x] `app/callbacks.py` 공유 콜백 분리 (`_load_knowledge`, `_before/after_agent_callback`, `_after_tool_callback`)

### 6-2. simulation_agent (신규 — 피어) ✅ 완료 (2026-05-31)
- [x] `simulation_agent` 구현 완료
  - 도구: `calculate_tax_saving`, `calculate_maturity_amount`, `calculate_pension_payout`
  - 페르소나: 토리 🐿️ — 수치 계산 전담
  - `AgentTool(simulation_agent)` → `investment_agent`, `pension_tax_agent` 양쪽 등록
- [x] `app/simulation_agent.py` 별도 파일 분리

### 6-3. fraud_detection_agent (신규) ✅ 완료 (2026-05-31)
- [x] `fraud_detection_agent` 구현 완료
  - 도구: `check_fraud_pattern(text)` — 6대 사기 유형 패턴 DB 기반 위험도 판정
  - 페르소나: 호야 🐯 — 침착하고 단호한 보안 전문가
  - RULE 0: 사기 키워드 감지 시 barrier_free_agent가 즉시 위임
- [x] `app/fraud_detection_agent.py` 별도 파일 분리

### 6-4. customer_management_agent (신규 — 백그라운드)
- [ ] `app/customer_management_agent.py` 생성
  - 역할: 대화 종료 후 `memory/users/{user_id}.md` 업데이트, 피드백 루프 관리
  - 관리자가 ADK playground에서 "사용자 현황 보고해줘" 로 조회 가능
  - 별도 `admin_app = App(root_agent=customer_management_agent, name="admin")` 으로 분리

### 6-5. system_improvement_agent (신규 — 백그라운드)
- [ ] `app/system_improvement_agent.py` 생성
  - 역할: `memory/agents/` 하위 스킬 문서 주기적 정리·병합·삭제 (Hermes 스킬 큐레이터)
  - 7일 주기 또는 스킬 문서 10개 누적 시 실행
  - 관리자가 ADK playground에서 "스킬 업데이트 현황 보고해줘" 로 조회 가능

### 6-6. 에이전트 페르소나 추가 ✅ 완료 (2026-05-31)

> **BF Agent** — *Best Friend & Barrier Free*

- [x] 전 에이전트 instruction에 이름·성격·말투 가이드 블록 추가
  - `barrier_free_agent` → **"뭉치"** 🐕 (둥글둥글 순한 백구)
  - `investment_agent` → **"나비"** 🐱 (빠르고 영리한 고양이)
  - `pension_tax_agent` → **"까치"** 🐦 (좋은 소식을 물어오는 길조)
  - `simulation_agent` → **"토리"** 🐿️ (작지만 야무진 다람쥐)
  - `fraud_detection_agent` → **"호야"** 🐯 (든든하고 용맹한 호랑이)

### 6-7. 프롬프트 다이어트 ✅ 완료 (2026-05-28)
- [x] `pension_tax_agent`: 용어사전(`{_glossary_wiki}`) 중복 주입 제거 (~1,038 토큰)
- [x] `investment_agent`: `[핵심 원칙]` + `[도구 사용 지침]` 압축
- [x] `barrier_free_agent`: 내비게이션 규칙·금지 표현 목록·도구 응답 처리 규칙 압축
