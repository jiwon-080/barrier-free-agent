"""
KRX ETF 실시간 가격·NAV 조회 도구 (FinanceDataReader 기반)

에이전트가 ETF 현재 시세를 물어볼 때 호출합니다.
"""

import FinanceDataReader as fdr


def get_etf_price(ticker_or_name: str) -> dict:
    """
    ETF 현재가·NAV 실시간 조회

    Args:
        ticker_or_name: ETF 종목코드(6자리) 또는 종목명 (예: "069500" / "KODEX 200")

    Returns:
        {
            "ticker":      "069500",
            "name":        "KODEX 200",
            "price":       "31250",
            "nav":         "31240",
            "change_rate": "0.48",
            "volume":      "1234567",
            "summary":     "KODEX 200 현재가는 31,250원 (NAV 31,240원, +0.48%)입니다."
        }
    """
    df = fdr.StockListing("ETF/KR")
    query = ticker_or_name.strip()

    match = df[df["Symbol"] == query]
    if match.empty:
        match = df[df["Name"].str.contains(query, na=False)]

    if match.empty:
        return {
            "error":   f"'{query}'에 해당하는 ETF를 찾을 수 없습니다.",
            "summary": f"'{query}' ETF 정보를 조회할 수 없습니다.",
        }

    row = match.iloc[0]
    ticker  = str(row.get("Symbol", ""))
    name    = str(row.get("Name", ""))
    price   = row.get("Price", "")
    nav     = row.get("NAV", "")
    rate    = row.get("ChangeRate", "")
    volume  = row.get("Volume", "")

    try:
        summary = (
            f"{name} 현재가는 {int(price):,}원"
            + (f" (NAV {int(float(nav)):,}원" if nav else "")
            + (f", {float(rate):+.2f}%)" if rate else ")")
            + "입니다."
        )
    except (ValueError, TypeError):
        summary = f"{name} 시세를 조회했습니다."

    return {
        "ticker":      ticker,
        "name":        name,
        "price":       str(price),
        "nav":         str(nav) if nav else "",
        "change_rate": str(rate),
        "volume":      str(volume),
        "summary":     summary,
    }


def get_etf_prices_by_keyword(keyword: str) -> list[dict]:
    """
    종목명 키워드로 ETF 검색 후 시세 반환 (최대 5개)

    Args:
        keyword: 검색 키워드 (예: "KODEX", "채권", "레버리지")
    """
    df = fdr.StockListing("ETF/KR")
    matched = df[df["Name"].str.contains(keyword, na=False)].head(5)

    result = []
    for _, row in matched.iterrows():
        result.append({
            "ticker":      str(row.get("Symbol", "")),
            "name":        str(row.get("Name", "")),
            "price":       str(row.get("Price", "")),
            "nav":         str(row.get("NAV", "")),
            "change_rate": str(row.get("ChangeRate", "")),
        })
    return result


if __name__ == "__main__":
    result = get_etf_price("069500")
    print(result.get("summary", result))
