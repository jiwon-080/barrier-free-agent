# UIUX TODO — NH 배리어프리 에이전트 데모 리빌드
> 기준 이미지: `data/images/` (main_normal, main_bigtext_mode, menu_bigtext_mode, chatbot_1, 금융상품 등)
> 유지: SCREEN_MAP 라우팅 구조, 하이라이트 CSS 애니메이션, 동의 UI 패턴, NH_GREEN 상수, session_state 구조

---

## 1. 레이아웃 — 하단 탭바 (최우선)

> 실제 앱: 항상 고정된 하단 탭 (홈 / 금융상품 / 내자산 / 포인트쌓기 / 생활혜택)
> 현재 demo.py: 없음 → 화면 이동 방법이 불분명함

- [ ] `st.components.v1.html` 또는 CSS `position: fixed; bottom: 0`으로 하단 탭바 구현
- [ ] 탭 항목: **홈 / 금융상품 / 내자산** (데모 범위 3개로 축소)
- [ ] 현재 탭 활성 상태 표시 (NH_GREEN 아이콘 + 텍스트)
- [ ] 탭 클릭 → `session_state["current_route"]` 변경 + `st.rerun()`

---

## 2. 홈 화면 개선

> 실제 앱: 계좌카드 + 퀵메뉴 아이콘 그리드 + 큰글 토글(우측 상단)
> 현재 demo.py: 배리어프리 배너가 홈에 박혀 있어 어색함

- [ ] 우측 상단 **큰글 토글** → `session_state["bigtext_mode"]` bool로 관리
- [ ] 큰글 모드 ON 시: 배너 "배리어프리 도우미에게 물어보세요" + 큰 버튼 2개(전체계좌조회 / ATM출금) → bigtext 전용 홈 레이아웃으로 분기
- [ ] 퀵메뉴 아이콘 그리드: 올원계좌등록 / 전체계좌조회 / 공과금납부 / 알뜰환전 (실제 앱과 동일 구성)
- [ ] 배리어프리 도우미 배너는 홈에서 제거 → **에이전트는 FAB 버튼 + 하단 팝업**으로 대체 (섹션 5 참조)

---

## 3. 금융상품 화면 — 아이콘 그리드

> 실제 앱: 컬러 아이콘 2×4 그리드 (입출금/예금/적금/주택청약/펀드/대출/외환/퇴직연금/신탁/ISA/보험/골드실버바)
> 현재 demo.py: 텍스트 리스트 (`menu_item()`) → 실제 앱과 전혀 다름

- [ ] `st.columns(4)` 기반 아이콘 그리드로 교체
- [ ] 각 항목: 이모지 아이콘 + 한글 라벨 + 버튼 클릭 시 route 이동
- [ ] 상단 배너 슬롯 (추천 상품 1개, 고정 텍스트로 대체 가능)
- [ ] 해시태그 칩 필터 (#사회초년생 / #직장인 / #개인사업자) — 클릭해도 현재는 동작 없어도 됨 (시각적 완성도용)
- [ ] **ISA 화면** 추가: `screen_isa()` + SCREEN_MAP 등록 + navigation_tool의 `financial_products/isa` route 연결

---

## 4. 큰글 모드 — 실제 동작

> 실제 앱: 큰글 ON 시 완전히 다른 레이아웃 (폰트 대형화, 메뉴 단순화, 큰글도우미 배너)
> 현재 demo.py: 토글 UI만 있고 아무것도 안 바뀜

- [ ] `session_state["bigtext_mode"]` → 모든 화면에서 분기 처리
- [ ] 큰글 모드 CSS: `font-size` 전체 +4px, 버튼 높이 +50%, 여백 확대
- [ ] 큰글 모드 메뉴: 항목 수 축소 (핵심 5개만), 아이콘 + 텍스트 크게
- [ ] 큰글 모드 홈: "**배리어프리 도우미에게 물어보세요**" 배너 버튼 → FAB 버튼 클릭과 동일하게 팝업 오픈

---

## 5. 에이전트 — FAB 버튼 + 하단 팝업 (핵심)

> 별도 채팅 페이지로 이동하지 않음. 현재 화면 위에 오버레이로 뜨는 방식.
> 사용자가 지금 보고 있는 화면을 유지한 채로 질문하고, 에이전트가 그 자리에서 답하거나 이동 제안.

### 5-1. FAB (플로팅 동그란 버튼)
- [ ] 모든 화면에 항상 표시: `position: fixed; bottom: 72px; right: 16px` (하단 탭바 위)
- [ ] 디자인: NH_GREEN 원형 버튼, 로봇/마이크 아이콘, 그림자 효과
- [ ] 상태 표시: 기본(초록) / 에이전트 응답 대기 중(펄스 애니메이션) / 팝업 열림(X 아이콘으로 변경)
- [ ] `session_state["agent_popup_open"]` bool로 팝업 열림/닫힘 관리

### 5-2. 하단 팝업 (Bottom Sheet)
- [ ] FAB 클릭 → 아래에서 슬라이드업 되는 팝업 (CSS `transform: translateY` + `transition`)
- [ ] 팝업 높이: 화면의 약 60% (`max-height: 60vh`)
- [ ] **상단 — 에이전트 소개 영역** (최초 1회 또는 대화 없을 때):
  - 로봇 아이콘 + "안녕하세요, 배리어프리 도우미입니다 🤖"
  - 예시 질문 칩 3개: `IRP가 뭔가요?` / `기준금리 알려줘` / `퇴직연금 가입하고 싶어요`
  - 예시 칩 클릭 → 해당 텍스트로 즉시 질문 전송
- [ ] **중간 — 대화 내역** (질문/답변이 생기면 스크롤 가능하게 표시):
  - 사용자 발화: 우측 정렬, NH_GREEN 말풍선
  - 에이전트 답변: 좌측 정렬, 회색 카드
  - navigate 결과 있을 경우: "📍 **퇴직연금** 화면으로 이동할까요?" 인라인 카드 + **예 / 아니오** 버튼
    - 예 → 팝업 닫힘 + route 이동 + highlight_target 적용 (기존 CSS 애니메이션 유지)
    - 아니오 → 카드 사라지고 대화 계속
- [ ] **하단 — 입력 영역** (팝업 내 고정):
  - `[      무엇이든 물어보세요      ] [🎤]`
  - 텍스트 입력 또는 마이크 버튼으로 음성 입력 (섹션 7 STT 연동)
- [ ] 팝업 바깥 영역 클릭 또는 X 버튼 → 팝업 닫힘 (대화 내역은 session_state 유지)

---

## 6. ADK Agent 실제 연동

> 현재 demo.py: `navigate_ui`를 직접 호출 → 용어설명·상품조회·가드레일이 UI에서 작동 안 함

- [ ] `google.adk.runners.InMemoryRunner` 로 `barrier_free_agent` 실행
- [ ] `asyncio.run()` 또는 `asyncio.get_event_loop().run_until_complete()` 로 Streamlit 내 비동기 처리
- [ ] 응답 파싱:
  - `event.get_function_calls()` 중 `navigate_ui` → route + highlight 추출
  - `event.text` → 말풍선 텍스트
- [ ] 로딩 중 `st.spinner("도우미가 답변을 준비하고 있습니다...")` 표시

---

## 7. STT / TTS 연동

> 실제 앱 큰글도우미: 입력창 우측 마이크 버튼(파란 원) → 음성 입력
> 목표: 음성 쿼리 → STT → 에이전트 → TTS 응답 + 화면 이동

### STT (음성 입력)
- [ ] 브라우저 Web Speech API (`webkitSpeechRecognition`) — JS snippet을 `st.components.v1.html`로 삽입
- [ ] 인식된 텍스트 → `st.query_params` 또는 `st.session_state`에 주입 후 `st.rerun()`
- [ ] 마이크 버튼 UI: 대기 중(파란 원) / 녹음 중(빨간 원 + 펄스 애니메이션) 상태 구분

### TTS (음성 출력)
- [ ] `gTTS(text, lang='ko')` → `BytesIO` → `st.audio(bytes, format='audio/mp3', autoplay=True)`
- [ ] 에이전트 응답마다 자동 재생 (autoplay=True)
- [ ] 큰글 모드에서만 TTS 자동 재생, 일반 모드는 수동 재생 버튼으로 구분 (선택)

---

## 8. 화면별 나머지 보완

| 화면 | 할 일 |
|------|-------|
| `screen_isa()` | ISA 신탁형/일임형 탭 + 주요 정보 카드 (신규 추가) |
| `screen_retirement_pension()` | 텍스트 리스트 → 아이콘 리스트로 교체 |
| `screen_irp_tax_saving()` | 실제 앱처럼 체크리스트 형태 유지 (현재 양호) |
| `screen_my_pension()` | 현재 양호, 유지 |
| `screen_portfolio()` | 현재 양호, 유지 |

---

## 우선순위 요약

```
🔴 P0 (데모 필수)
  5-1. FAB 플로팅 버튼
  5-2. 하단 팝업 (소개 + 대화 + 입력창)
  6.   ADK Agent 실제 연동

🟡 P1 (완성도)
  1.   하단 탭바
  3.   금융상품 아이콘 그리드 + ISA 화면
  4.   큰글 모드 실제 동작
  7.   TTS (gTTS, 에이전트 응답 자동 재생)
  7.   STT (Web Speech API 마이크 버튼)

🟢 P2 (있으면 좋음)
  2.   홈 화면 세부 개선
  8.   화면별 나머지 보완
```
