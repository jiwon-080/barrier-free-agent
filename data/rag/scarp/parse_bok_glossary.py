"""
한국은행 경제금융용어 700선 PDF 파싱 스크립트
입력: data/rag/2023_경제금융용어 700선-게시(저용량).pdf
출력: data/rag/bok_glossary.json
"""

import json
import re
import sys
import io
from pathlib import Path

import pdfplumber

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF_PATH = Path(__file__).parent.parent / "2023_경제금융용어 700선-게시(저용량).pdf"
OUTPUT_PATH = Path(__file__).parent.parent / "bok_glossary.json"

CONTENT_START_PAGE = 16  # 0-indexed (17페이지부터 본문)

# 페이지 헤더/푸터로 쓰이는 고정 문자열 제거
_SKIP_LINES = {"경제금융용어 700선", "찾아보기"}
_HANGUL_CONSONANTS = set("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ")
_CONSONANT_SUFFIX_RE = re.compile(r"\s+[ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ]$")  # "기준금리 ㄱ" 제거용
_PAGE_NUM_RE = re.compile(r"^\d{1,3}$")
_RELATED_RE = re.compile(r"^연관검색어\s*[:：]\s*(.+)$")


def _clean_lines(raw_text: str) -> list[str]:
    """텍스트를 줄 단위로 분리하고 불필요한 줄 제거"""
    lines = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line in _SKIP_LINES:
            continue
        if line in _HANGUL_CONSONANTS:  # 'ㄱ', 'ㄴ' 등 자음 인덱스 마커
            continue
        if _PAGE_NUM_RE.match(line):
            continue
        lines.append(line)
    return lines


def _is_term_heading(line: str, next_line: str | None) -> bool:
    """
    용어 제목 줄 판별 기준:
    - 줄 자체가 짧다 (40자 이하)
    - 마침표·쉼표로 끝나지 않음
    - 다음 줄이 존재하고 그 줄이 문장처럼 시작함
    """
    if len(line) > 40:
        return False
    if line.endswith((".", ",", "다.", "다,", "며", "고")):
        return False
    if next_line and (
        next_line[0].islower()
        or next_line.startswith("가구")
        or re.match(r"^[가-힣]", next_line)
    ):
        return True
    return False


def extract_terms(pdf_path: Path) -> list[dict]:
    """PDF 전체 텍스트에서 용어·정의·연관검색어 추출"""
    all_lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"총 {total}페이지, 본문 시작: {CONTENT_START_PAGE + 1}페이지")
        for page_num in range(CONTENT_START_PAGE, total):
            text = pdf.pages[page_num].extract_text() or ""
            all_lines.extend(_clean_lines(text))

    print(f"전체 줄 수: {len(all_lines)}")

    terms_map: dict[str, dict] = {}  # term → entry (더 긴 정의 우선 보존)
    current_term: str | None = None
    current_def_lines: list[str] = []
    current_related: list[str] = []

    def flush():
        if current_term and current_def_lines:
            definition = " ".join(current_def_lines).strip()
            existing = terms_map.get(current_term)
            # 더 긴 정의를 가진 쪽 유지 (section-marker 오파싱 제거 효과)
            if not existing or len(definition) > len(existing["official_definition"]):
                terms_map[current_term] = {
                    "term": current_term,
                    "official_definition": definition,
                    "related_terms": current_related,
                    "source": "한국은행 경제금융용어 700선(2023)",
                }

    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        next_line = all_lines[i + 1] if i + 1 < len(all_lines) else None

        # 연관검색어 줄
        related_match = _RELATED_RE.match(line)
        if related_match:
            current_related = [t.strip() for t in re.split(r"[,，、]", related_match.group(1))]
            i += 1
            continue

        # 용어 제목 판별
        if _is_term_heading(line, next_line):
            flush()
            # "기준금리 ㄱ" 형태의 trailing 자음 마커 제거
            current_term = _CONSONANT_SUFFIX_RE.sub("", line).strip()
            current_def_lines = []
            current_related = []
            i += 1
            continue

        # 정의 본문 누적
        if current_term is not None:
            current_def_lines.append(line)

        i += 1

    flush()

    # 자음 suffix 항목 제거 ("기준금리 ㄱ" 등 section 마커가 term에 붙은 오파싱 결과)
    _bad_suffix = re.compile(r"\s+[ㄱ-ㅎ]$")
    clean = [t for t in terms_map.values() if not _bad_suffix.search(t["term"])]
    return clean


def merge_with_fss(bok_terms: list[dict], fss_path: Path) -> list[dict]:
    """FSS 사전과 병합. 중복 시 BOK 우선."""
    _bad_suffix = re.compile(r"[ㄱ-ㅎ]$")
    try:
        with open(fss_path, encoding="utf-8") as f:
            fss_data = json.load(f)
        # 이전 파싱 오류로 남은 자음 suffix 항목 제거 + BOK 출처 항목 제외 (재병합 방지)
        fss_terms = [
            d for d in fss_data
            if "term" in d
            and not _bad_suffix.search(d["term"])
            and d.get("source", "") != "한국은행 경제금융용어 700선(2023)"
        ]
    except Exception:
        fss_terms = []

    bok_term_set = {t["term"] for t in bok_terms}
    fss_unique = [t for t in fss_terms if t["term"] not in bok_term_set]

    merged = bok_terms + fss_unique
    print(f"\nBOK: {len(bok_terms)}개 / FSS 고유: {len(fss_unique)}개 / 합계: {len(merged)}개")
    return merged


def main():
    print("=== BOK PDF 파싱 시작 ===")
    terms = extract_terms(PDF_PATH)
    print(f"\n추출된 용어 수: {len(terms)}개")

    # 샘플 출력
    print("\n--- 샘플 (앞 3개) ---")
    for t in terms[:3]:
        print(f"[{t['term']}] {t['official_definition'][:80]}...")
        print(f"  연관: {t['related_terms']}")

    # bok_glossary.json 저장
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)
    print(f"\nBOK 사전 저장: {OUTPUT_PATH}")

    # FSS와 병합 → fss_bok_glossary.json 갱신
    fss_path = OUTPUT_PATH.parent / "fss_bok_glossary.json"
    merged = merge_with_fss(terms, fss_path)

    merged_path = OUTPUT_PATH.parent / "fss_bok_glossary.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"병합 사전 저장: {merged_path}")


if __name__ == "__main__":
    main()
