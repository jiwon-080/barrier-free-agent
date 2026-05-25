# 지식베이스 데이터 소스 목록

`data/knowledge/` 마크다운 작성에 사용할 원본 소스 후보.
크롤링 가능 여부를 검증하며 ❌ 항목을 제거해나간다.

**범례**
- ✅ 크롤링/수집 가능 확인
- ⚠️ 조건부 (JS 렌더링 필요 or 인증키 필요)
- ❌ 불가 (robots.txt 차단, 로그인 필수, 동적 전용)
- 📝 수동 작성 (공개 보고서·법령 기반)

---

## 공용 (glossary/) — 금융 용어

| # | 소스 | URL | 유형 | 상태 | 비고 |
|---|------|-----|------|------|------|
| G1 | 한국은행 경제금융용어 700선 PDF | `data/source/documents/` | PDF | ✅ | 이미 보유. pdfplumber로 추출 |
| G2 | 국가법령정보센터 오픈API | https://open.law.go.kr | REST API | ⚠️ | 무료 키 발급 필요. 소득세법·근로자퇴직급여보장법 조문 추출 가능 |
| G3 | 한국은행 경제통계시스템 ECOS API | https://ecos.bok.or.kr/api/ | REST API | ⚠️ | 무료 키 발급 필요. 기준금리·환율·CPI 등 수치 데이터 |

---

## investment/ — 투자·상품·시장

| # | 소스 | URL | 유형 | 상태 | 비고 |
|---|------|-----|------|------|------|
| I1 | 한국거래소 KRX (pykrx) | https://www.krx.co.kr | 라이브러리 | ✅ | 이미 사용 중. ETF 종목·시세·편입종목 |
| I2 | 금융감독원 공공데이터 (예금·적금 상품) | https://www.data.go.kr | REST API | ⚠️ | data.go.kr 키 발급 필요. 금감원 제공 상품 비교 데이터 |
| I3 | 금융감독원 파인(FINE) 금융상품 비교 | https://fine.fss.or.kr | JS 렌더링 | ⚠️ | 비교 페이지는 JS. 단, data.go.kr API로 동일 데이터 접근 가능 (I2와 중복) |
| I4 | 금융투자협회 KOFIA 펀드정보 | https://www.kofia.or.kr | JS 렌더링 | ⚠️ | 전자공시 DART에서 펀드 공시 대체 가능 |
| I5 | 금융감독원 DART 오픈API | https://opendart.fss.or.kr | REST API | ⚠️ | 무료 키 발급 필요. 펀드·ETF 운용보고서 |
| I6 | 한국은행 ECOS API (거시경제) | https://ecos.bok.or.kr/api/ | REST API | ⚠️ | G3과 동일. 기준금리·M2·GDP 등 |
| I7 | 예금보험공사 예금자보호 안내 | https://www.kdic.or.kr | 정적 HTML | ✅ | 5,000만 원 한도 등 보호 내용. 정적 렌더링 확인 필요 |
| I8 | 은행연합회 소비자포털 상품 공시 | https://portal.kfb.or.kr | JS 렌더링 | ⚠️ | 예·적금 금리 공시. JS 렌더링으로 Selenium 필요 |

---

## pension_tax/ — 퇴직연금·IRP·ISA·절세

| # | 소스 | URL | 유형 | 상태 | 비고 |
|---|------|-----|------|------|------|
| P1 | 국세청 연금계좌 세액공제 안내 | https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875 | 정적 HTML | ✅ | 세액공제 한도·공제율 수치 완전 포함 확인. 직접 크롤링 가능 |
| P2 | 국세청 2025 귀속 연말정산 종합 안내 | https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2304&cntntsId=238938 | 정적 HTML | ✅ | IRP·ISA·연금저축 절세 내용 포함 |
| P3 | 고용노동부 퇴직연금 종합안내 | https://www.moel.go.kr/retirementpay.do | 정적 HTML | ✅ | DB형·DC형·IRP 구분 설명 정적 포함 확인 |
| P4 | 국가법령정보센터 — 근로자퇴직급여보장법 | https://open.law.go.kr | REST API | ⚠️ | G2와 동일 API. 퇴직연금 관련 법조문 |
| P5 | 국가법령정보센터 — 소득세법 (연금계좌 조항) | https://open.law.go.kr | REST API | ⚠️ | G2와 동일 API |
| P6 | 금융감독원 공공데이터 — IRP 상품 | https://www.data.go.kr | REST API | ⚠️ | I2와 동일 키. IRP 상품 비교 데이터 |
| P7 | 금융감독원 파인(FINE) — 연금저축 비교 | https://fine.fss.or.kr | JS 렌더링 | ⚠️ | data.go.kr API로 대체 가능 |

---

## fraud/ — 금융사기·보이스피싱

| # | 소스 | URL | 유형 | 상태 | 비고 |
|---|------|-----|------|------|------|
| F1 | 금융감독원 보이스피싱 보도자료 | https://www.fss.or.kr/fss/bbs/B0000052/list.do?menuNo=200358 | JS 렌더링 | ⚠️ | 목록·본문 모두 JS. PDF 보도자료 직접 다운로드는 가능 |
| F2 | 금융감독원 연간 보이스피싱 피해현황 PDF | https://www.fss.or.kr (보도자료 첨부) | PDF | ⚠️ | 매년 발간. URL 직접 수집 필요. pdfplumber로 추출 가능 |
| F3 | 정부24 보이스피싱 예방 행동요령 | https://www.gov.kr | 정적 HTML | ✅ | 정부24는 대부분 정적. 유형별 행동요령 포함 |
| F4 | 수동 작성 — FSS 분류 기준 (6대 유형) | — | 📝 | 📝 | 기관사칭형·대출빙자형·납치협박형·메신저피싱·스미싱·투자빙자형. 공개 보도자료 기반 |

---

## wiki_admin/ — 관리 전용 (소스 불필요)

자동 생성 또는 에이전트가 직접 작성. 외부 소스 없음.

---

## 수집 우선순위

| 순위 | 소스 | 이유 |
|------|------|------|
| 1 | G1 — BOK PDF (이미 보유) | pdfplumber 즉시 추출 가능 |
| 2 | P1, P2 — 국세청 정적 HTML | ✅ 확인 완료. IRP·ISA 핵심 수치 |
| 3 | I1 — KRX (pykrx) | 이미 코드 있음 |
| 4 | F4 — fraud 수동 작성 | FSS 크롤 불가, 직접 작성이 현실적 |
| 6 | G2, P4, P5 — law.go.kr API | 법령 조문 정확도 필요 시 |
| 7 | G3, I6 — ECOS API | 거시지표 실시간 필요 시 |
| 8 | I2, P6 — data.go.kr 금감원 API | 상품 데이터 실시간 필요 시 |

---

## 제거 후보

- **I3 파인(FINE) 직접 크롤** ❌ — I2 data.go.kr API로 대체
- **P7 파인(FINE) 연금저축** ❌ — P6 data.go.kr API로 대체
