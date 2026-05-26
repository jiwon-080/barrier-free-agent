"""
KRX ETF 종목 메타데이터 수집 → RAG 사전(krx_etf_info.json) 저장

FinanceDataReader를 사용합니다.
(data.krx.co.kr은 최근 세션 인증 강화로 직접 접근 불가 → fdr이 우회 경로 제공)

사용법:
    uv run python data/rag/scarp/scrap_krx.py            # 실제 수집
    uv run python data/rag/scarp/scrap_krx.py --dry-run  # 상위 3건 확인

갱신 주기: 하루 1회
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import FinanceDataReader as fdr

OUT_PATH = Path(__file__).parent.parent / "krx_etf_info.json"

# ETF 카테고리 코드 → 유형명 + 위험등급
# fdr의 Category 필드: 1=국내주식, 2=채권, 3=원자재, 4=해외주식, 5=파생, 6=기타
CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "1": ("국내주식", "보통"),
    "2": ("채권",     "낮음"),
    "3": ("원자재",   "높음"),
    "4": ("해외주식", "높음"),
    "5": ("파생",     "매우높음"),
    "6": ("기타",     "보통"),
}

# 종목명 키워드 추가 보정
KEYWORD_RISK: dict[str, str] = {
    "레버리지": "매우높음",
    "인버스":   "매우높음",
    "2X":       "매우높음",
    "3X":       "매우높음",
}


def _resolve_risk(category_code: str, name: str) -> tuple[str, str]:
    """(유형명, 위험등급) 반환"""
    cat_name, risk = CATEGORY_MAP.get(str(category_code), ("기타", "보통"))
    for kw, kw_risk in KEYWORD_RISK.items():
        if kw in name:
            risk = kw_risk
            break
    return cat_name, risk


def transform_to_glossary(df) -> list[dict]:
    today = datetime.today().strftime("%Y-%m-%d")
    result = []

    for _, row in df.iterrows():
        ticker   = str(row.get("Symbol", "")).strip()
        name     = str(row.get("Name",   "")).strip()
        cat_code = str(row.get("Category", "")).strip()
        nav      = row.get("NAV", "")
        price    = row.get("Price", "")

        if not name or not ticker:
            continue

        cat_name, risk = _resolve_risk(cat_code, name)
        nav_str = f" 최근 NAV(순자산가치): {int(nav):,}원." if nav and nav == nav else ""  # NaN 제외

        try:
            nav_str = f" 최근 NAV(순자산가치): {int(float(nav)):,}원." if nav else ""
        except (ValueError, TypeError):
            nav_str = ""

        definition = (
            f"{name}은(는) KRX에 상장된 {cat_name} ETF입니다."
            f" 종목코드: {ticker}.{nav_str}"
            f" 투자위험등급: {risk}."
        )

        result.append({
            "term":                name,
            "isin":                ticker,
            "official_definition": definition,
            "category":            cat_name,
            "risk_level":          risk,
            "nav":                 str(nav) if nav else "",
            "source":              "KRX (FinanceDataReader)",
            "updated_at":          today,
        })

    return result


def main(dry_run: bool = False) -> None:
    print("[KRX] ETF 종목 목록 조회 중 (FinanceDataReader)...")
    df = fdr.StockListing("ETF/KR")
    print(f"[KRX] {len(df)}개 ETF 수신")

    if dry_run:
        print("\n=== [DRY-RUN] 상위 3건 ===")
        print(df.head(3).to_string())
        return

    print("[KRX] RAG 사전 변환 중...")
    glossary = transform_to_glossary(df)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False, indent=2)

    print(f"[KRX] 완료: {len(glossary)}개 항목 → {OUT_PATH}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
