# UIUX TODO — NH 배리어프리 에이전트 데모 리빌드
> 기준 이미지: `data/images/` (main_normal, main_bigtext_mode, menu_bigtext_mode, chatbot_1, 금융상품 등)
> 유지: SCREEN_MAP 라우팅 구조, 하이라이트 CSS 애니메이션, 동의 UI 패턴, NH_GREEN 상수, session_state 구조

---

## 1. 레이아웃 — 하단 탭바 (최우선) ✅ 완료 (2026-05-31)

- [x] CSS `position: fixed; bottom: 0`으로 하단 탭바 구현
- [x] 탭 항목: **홈 / 금융상품 / 내자산** (3개)
- [x] 현재 탭 활성 상태 표시 (NH_GREEN + border-top)
- [x] 탭 클릭 → `session_state["current_route"]` 변경 + `st.rerun()`

---

## 2. 홈 화면 개선

> 실제 앱: 계좌카드 + 퀵메뉴 아이콘 그리드 + 큰글 토글(우측 상단)
> 현재 demo.py: 배리어프리 배너가 홈에 박혀 있어 어색함

- [ ] 우측 상단 **큰글 토글** → `session_state["bigtext_mode"]` bool로 관리
- [ ] 큰글 모드 ON 시: 배너 "배리어프리 도우미에게 물어보세요" + 큰 버튼 2개(전체계좌조회 / ATM출금) → bigtext 전용 홈 레이아웃으로 분기
- [x] 퀵메뉴 아이콘 그리드 구현 (전체계좌조회 / ATM출금 / 금융상품 / 안전한금융)
- [ ] 배리어프리 도우미 배너는 홈에서 제거 → **에이전트는 FAB 버튼 + 하단 팝업**으로 대체 (섹션 5 참조)

---

## 3. 금융상품 화면 — 아이콘 그리드 ✅ 완료 (2026-05-31)

- [x] `st.columns(4)` 기반 아이콘 그리드로 교체
- [x] 각 항목: 이모지 아이콘 + 한글 라벨 + 버튼 클릭 시 route 이동
- [ ] 상단 배너 슬롯 (추천 상품 1개, 고정 텍스트로 대체 가능)
- [x] 해시태그 칩 필터 (#사회초년생 / #직장인 / #개인사업자) — 시각적 완성도용
- [x] **ISA 화면** 추가: `screen_isa()` + SCREEN_MAP 등록 + navigation_tool 연결

---

## 4. 큰글 모드 — 실제 동작

> 실제 앱: 큰글 ON 시 완전히 다른 레이아웃 (폰트 대형화, 메뉴 단순화, 큰글도우미 배너)
> 현재 demo.py: 토글 UI만 있고 아무것도 안 바뀜

- [ ] `session_state["bigtext_mode"]` → 모든 화면에서 분기 처리
- [ ] 큰글 모드 CSS: `font-size` 전체 +4px, 버튼 높이 +50%, 여백 확대
- [ ] 큰글 모드 메뉴: 항목 수 축소 (핵심 5개만), 아이콘 + 텍스트 크게
- [ ] 큰글 모드 홈: "**배리어프리 도우미에게 물어보세요**" 배너 버튼 → FAB 버튼 클릭과 동일하게 팝업 오픈

---

## 5. 에이전트 — FAB 버튼 + 하단 팝업 ✅ 완료 (2026-05-31)

### 5-1. FAB (플로팅 동그란 버튼) ✅
- [x] 모든 화면에 항상 표시: `position: fixed; bottom: 72px; right: 16px`
- [x] 디자인: NH_GREEN 원형 버튼, 그림자 효과
- [x] `@st.dialog` 기반 팝업 열림/닫힘 관리

### 5-2. 하단 팝업 (Bottom Sheet) ✅
- [x] FAB 클릭 → 슬라이드업 팝업 (CSS `transform: translateY` + `transition`)
- [x] 팝업 높이: 화면의 약 65% (`max-height: 65vh`)
- [x] 상단 에이전트 소개 영역 (최초 방문 시)
- [x] 예시 질문 칩 4개 (클릭 → 즉시 질문 전송)
- [x] 대화 내역 (사용자 우측/에이전트 좌측 말풍선)
- [x] navigate 결과 → 인라인 카드 + 예/아니오 버튼
- [x] 입력 영역 (텍스트 + 마이크 버튼)

---

## 6. ADK Agent 실제 연동 ✅ 완료 (2026-05-31)

- [x] `InMemoryRunner` 로 `barrier_free_agent` 실행
- [x] 동기 이벤트 루프로 Streamlit 내 처리
- [x] 응답 파싱: `get_function_calls()` → navigate_ui / get_isa_info / get_irp_info 구조화
- [x] `event.is_final_response()` → 말풍선 텍스트
- [x] 로딩 중 thinking card 표시 (도구별 라벨)

---

## 7. STT / TTS 연동 ✅ 완료 (2026-05-31)

### STT (음성 입력) ✅
- [x] `streamlit_mic_recorder.speech_to_text` — Web Speech API 래퍼
- [x] 인식된 텍스트 → `session_state["pending_query"]`에 주입 후 `st.rerun()`
- [x] 마이크 버튼 UI (streamlit_mic_recorder 내장 상태 표시)

### TTS (음성 출력) ✅
- [x] `gTTS(text, lang='ko')` → `BytesIO` → `st.audio(autoplay=True)`
- [x] 에이전트 응답마다 자동 재생
- [ ] 큰글 모드에서만 TTS 자동 재생 (일반 모드는 수동) — 섹션 4 bigtext_mode 구현 후 연동

---

## 8. 화면별 나머지 보완 ✅ 완료 (2026-05-31)

| 화면 | 상태 |
|------|------|
| `screen_isa()` | ✅ 신탁형/일임형 탭 + 주요 정보 카드 + 가입 체크리스트 |
| `screen_retirement_pension()` | ✅ 아이콘 + menu_item 리스트 |
| `screen_irp_tax_saving()` | ✅ 체크리스트 형태 유지 |
| `screen_my_pension()` | ✅ 유지 |
| `screen_portfolio()` | ✅ 유지 |

---

## 우선순위 요약

```
🔴 P0 (데모 필수) — 완료
  5.   FAB + 하단 팝업 ✅
  6.   ADK Agent 실제 연동 ✅

🟡 P1 (완성도) — 미구현
  2.+4. 큰글 모드 실제 동작 (bigtext_mode 상태 + 레이아웃 분기)
  2.   홈 배너 제거 (FAB으로 완전 대체)

🟢 P2 (있으면 좋음)
  3.   금융상품 상단 배너 슬롯
  7.   큰글 모드 TTS 조건 (bigtext_mode 완료 후)
```
