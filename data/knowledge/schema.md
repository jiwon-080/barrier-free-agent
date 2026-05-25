# Knowledge Base Schema

BF Agent 지식베이스 작성·유지 지침. 에이전트가 페이지를 생성하거나 업데이트할 때 반드시 이 문서를 먼저 읽으세요.

---

## 디렉터리 구조

```
data/knowledge/
  schema.md          ← 이 파일. 작성 규칙 및 네이밍 컨벤션
  index.md           ← 전체 페이지 목록 (자동 생성 금지, 수동 관리)
  investment/        ← 나비(investment_agent) 도메인
  pension_tax/       ← 까치(pension_tax_agent) 도메인
  fraud/             ← 호야(fraud_detection_agent) 도메인
  glossary/          ← 공용 금융 용어 (에이전트 공유)
  wiki_admin/        ← 위키 건강 관리 및 에이전트 스킬 문서
```

---

## 파일 네이밍 규칙

- **언어**: 한국어 파일명 허용. 공백 대신 `_` 사용.
- **형식**: `개념명.md` (예: `IRP.md`, `기관사칭형.md`, `세액공제.md`)
- **약어 우선**: 통용 약어가 있으면 약어로 (ETF.md, IRP.md, ISA.md)
- **금지**: 날짜 접두어, 번호 접두어, CamelCase (날짜·순서는 frontmatter로 관리)

---

## 페이지 frontmatter

모든 페이지 최상단에 아래 frontmatter 포함:

```yaml
---
title: 페이지 제목
domain: investment | pension_tax | fraud | glossary
tags: [태그1, 태그2]
source: 출처 URL 또는 문서명 (없으면 생략)
last_updated: YYYY-MM-DD
importance: high | medium | low
---
```

`importance`는 wiki_admin 에이전트가 고아 페이지·저중요도 정리 시 기준으로 사용합니다.

---

## 본문 작성 규칙

1. **첫 문단**: 개념의 핵심을 2~3문장으로 요약 (LLM이 context로 주입할 때 앞부분만 읽어도 파악 가능하도록)
2. **위키링크**: 다른 페이지 참조 시 `[[페이지명]]` 형식 사용
3. **섹션 구조**: `##` 헤더로 구분, 깊이는 `###`까지만
4. **수치·법령**: 반드시 출처 명시 (`> 출처: ...` 블록쿼트)
5. **에이전트 주입 목적**: 서술형 문장 위주, 표는 핵심 비교에만 사용

---

## 위키링크 관계 정의

페이지 하단 `## 관련 항목` 섹션에 연관 페이지 나열:

```markdown
## 관련 항목
- [[IRP]] — 세액공제 혜택 제공 계좌
- [[세액공제]] — 납입금액 기준 환급 계산
```

---

## 업데이트 절차

1. 기존 페이지 수정 시: frontmatter `last_updated` 갱신
2. 새 페이지 추가 시: `index.md`에 항목 추가 필수
3. 페이지 삭제 시: `wiki_admin/log.md`에 삭제 사유 기록 후 `index.md`에서 제거
4. 출처 없는 내용 추가 금지 — 반드시 `data/source/` 문서 또는 공식 URL 기반

---

## 에이전트별 로드 범위

| 에이전트 | 로드할 디렉터리 |
|---|---|
| investment_agent (나비) | `investment/`, `glossary/` |
| pension_tax_agent (까치) | `pension_tax/`, `glossary/` |
| fraud_detection_agent (호야) | `fraud/` |
| barrier_free_agent (뭉치) | `glossary/` (필요 시) |
