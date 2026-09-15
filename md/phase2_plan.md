# Phase 2 개발 계획 — 로컬화 & 관리자 보드

> 기말 발표 완료 (2026-06-29) 이후 공모전 대비 2차 개발 방향.
> 지금 당장 구현보다 방향 정리 목적.

---

## 배경 및 제약 조건

- 실제 금융기관 적용 시 **망분리** 환경 가정
  - 외부 API(Gemini 등) 사용 불가 → 로컬 LLM 서빙 필요
  - 지식베이스 업데이트는 망간자료전송(단방향) 또는 수동 배포
  - ADK 프레임워크 자체는 오프라인 동작 가능 — 모델 엔드포인트만 교체
- 개인 GPU 없음 → 학습은 코랩 A100, 서빙은 종량제 GPU 클라우드(RunPod 등)
- 코랩 컴퓨팅 단위 약 50개 남음

---

## 1. 로컬 LLM 전환

### 1-1. 파인튜닝 모델 선정

| 모델 | 한국어 품질 | 라이선스 | 추천 사이즈 | 비고 |
|---|---|---|---|---|
| **EXAONE 3.5** | ⭐⭐⭐ | Apache 2.0 | 2.4B (안전) / 7.8B (고품질) | LG AI Research, 한국어 특화 |
| Gemma 3 | ⭐⭐ | 상업적 제한 | 4B | Google, 범용 |

→ **EXAONE 3.5 추천** (한국어 금융 상담 도메인, 공모전 라이선스 무제한)
→ 코랩 유닛 절약: 2.4B로 파이프라인 검증 후 7.8B 시도

### 1-2. 학습 데이터

우선순위:
1. **AI Hub 민원(콜센터) 질의-응답** — 110만 쌍, 상담 말투 학습 핵심
2. **AI Hub 금융·법률 문서 기계독해** — 40만 건 Q&A, 도메인 지식
3. **기존 `data/knowledge/*.md` 기반 Q&A 합성** — GPT로 질문-답변 쌍 생성, 빠르고 도메인 정확

→ AI Hub 신청 필요 (승인 1~3일). 합성 데이터는 당장 생성 가능.

### 1-3. 학습 절차

```
[코랩 A100]
QLoRA 학습 (EXAONE 3.5)
→ adapter.safetensors 저장
→ HuggingFace Hub 업로드

[RunPod / vast.ai — 데모 시에만 켬]
베이스모델 + adapter 로드
→ vLLM 서빙 (OpenAI 호환 엔드포인트)
→ ADK LiteLLM 연결
```

### 1-4. ADK 코드 변경 (최소화)

```python
# 현재 (Gemini API)
model=Gemini(model="gemini-3.5-flash")

# 로컬/클라우드 GPU 서빙 시
from google.adk.models.lite_llm import LiteLlm
model=LiteLlm(model="openai/exaone-3.5", api_base="https://your-runpod-endpoint")
```

에이전트 구조, 툴, 콜백 전혀 변경 없음.

---

## 2. 관리자 보드 (`admin_demo/`)

> 현재 데모(`ui/demo.py`)는 Streamlit Cloud 배포. 관리자 보드는 **로컬 전용**.
> 같은 레포지토리 `admin_demo/` 폴더에 공존. `streamlit run admin_demo/admin_app.py`

### 2-1. 현재 구현 완료 (2026-07-28)

- [x] `admin_demo/admin_app.py` — 탭 5개 구조
- [x] `📚 지식베이스` 탭 — 도메인/파일 선택, 인라인 에디터, 저장 시 `last_updated` 자동 갱신, 새 파일 생성(frontmatter 템플릿), 삭제(log.md 자동 기록)
- [x] `📄 PDF 업로드` 탭 — PDF → 마크다운 변환, 미리보기, 도메인 선택 후 저장
- [x] `📋 갱신 이력` 탭 — `wiki_admin/log.md` 편집, 수동 갱신 항목 빠른 기록, lint 리포트
- [x] `👤 고객 관리 에이전트` 탭 — `customer_management_agent` 채팅 UI (ADK InMemoryRunner)
- [x] `🧹 스킬 큐레이터` 탭 — `system_improvement_agent` 채팅 UI (ADK InMemoryRunner)
- [x] `admin_demo/utils/kb_utils.py` — 지식베이스 파일 CRUD
- [x] `admin_demo/utils/pdf_utils.py` — PDF 파싱 (pdfplumber / pypdf 자동 선택)
- [x] `admin_demo/utils/agent_runner.py` — ADK 에이전트 Streamlit 동기 실행 래퍼

### 2-2. 추후 추가 예정

- [ ] **LLM 보조 정리 버튼** — 지식베이스 파일 선택 후 "✨ LLM 정리" 클릭 시 내용 자동 정제
- [ ] **정형 정보 스케줄 설정** — 기준금리 등 갱신 주기 설정 및 마지막 갱신 시각 표시
- [ ] **에이전트 활성화 토글** — 나비·까치·호야 on/off, 프롬프트 수정
- [ ] **지식베이스 diff 뷰** — 저장 전 변경 사항 미리보기

---

## 3. 지식베이스 업데이트 전략 (망분리 대응)

현재 Wiki 패턴(파일 기반)은 망분리에 적합한 구조.

```
[인터넷망]                   [단방향 전송]     [내부망]
담당자 또는 배치 스크립트  ──────────►     에이전트 서버
└─ AI Hub 데이터 정제                      data/knowledge/
└─ 금감원 공시 수집                        └─ 파일 교체 → 재시작
└─ .md 파일 작성
```

- 변경 주기 낮은 데이터 (약관, 상품 설명): 수동 배포, 월 1회
- 변경 주기 높은 데이터 (금리 등): 배치 + 단방향 전송, 일 1회
- 관리자 보드 → 인터넷망 PC에서 실행 → 파일 작성 → 전송

---

## 4. 우선순위 및 순서

```
1단계 (즉시 가능)
  └─ AI Hub 데이터셋 신청 (민원 Q&A, 금융·법률 기계독해)
  └─ data/knowledge/ 기반 Q&A 합성 (GPT 활용)

2단계 (데이터 준비 후)
  └─ 코랩에서 EXAONE 3.5 2.4B QLoRA 파인튜닝 파이프라인 구축
  └─ 학습 검증 후 7.8B 시도

3단계 (서빙 테스트)
  └─ RunPod에서 vLLM 서빙 테스트
  └─ ADK LiteLlm 연결 확인
  └─ admin_demo 미구현 기능 추가
```
