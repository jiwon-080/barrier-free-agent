"""
한국은행 ECOS API 실시간 거시경제 지표 조회 도구
에이전트가 사용자 질문 시마다 호출 (저장 없음)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ECOS_API_KEY = os.getenv("ECOS_API_KEY")
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"

# ECOS 주요 통계 시리즈 코드
STAT_CODES = {
    "기준금리": ("722Y001", "0101000", "M"),   # (통계표코드, 항목코드, 주기)
    "CPI":      ("901Y009", "0",       "M"),   # 소비자물가지수
}

# 환율 (731Y001, 일별) - 통화별 항목코드
EXCHANGE_CODES = {
    "USD": "0000001",   # 미국 달러
    "JPY": "0000002",   # 일본 엔 (100엔 기준)
    "EUR": "0000003",   # 유로
    "GBP": "0000012",   # 영국 파운드
    "CAD": "0000013",   # 캐나다 달러
    "CHF": "0000014",   # 스위스 프랑 (안전자산)
    "AUD": "0000017",   # 호주 달러 (원자재 연동)
    "NZD": "0000026",   # 뉴질랜드 달러
    "HKD": "0000015",   # 홍콩 달러
    "SGD": "0000024",   # 싱가포르 달러
    "CNY": "0000053",   # 중국 위안
}


def _fetch_latest(stat_code: str, item_code: str, cycle: str) -> dict | None:
    """ECOS API에서 해당 지표의 최신값 1건 조회"""
    import datetime as dt
    today = dt.datetime.today()

    if cycle == "D":
        end = today.strftime("%Y%m%d")
        start = (today - dt.timedelta(days=10)).strftime("%Y%m%d")
    else:
        end = today.strftime("%Y%m")
        start = (today.replace(day=1) - dt.timedelta(days=90)).strftime("%Y%m")

    url = f"{BASE_URL}/{ECOS_API_KEY}/json/kr/1/5/{stat_code}/{cycle}/{start}/{end}/{item_code}"

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rows = data.get("StatisticSearch", {}).get("row", [])
        if rows:
            return rows[-1]  # 가장 최신 데이터
    except Exception:
        pass
    return None


def get_macro_indicators(indicators: list[str] | None = None) -> dict:
    """거시경제 지표 실시간 조회

    Args:
        indicators: 조회할 지표 목록. None이면 전체 조회.
                    가능한 값: "기준금리", "환율_USD", "CPI"

    Returns:
        {
            "기준금리": {"value": "3.50", "unit": "%", "period": "2026-03"},
            "환율_USD": {"value": "1380.00", "unit": "원", "period": "2026-03"},
            "CPI":      {"value": "114.21", "unit": "지수", "period": "2026-03"},
            "summary": "현재 기준금리는 3.50%이며, 원/달러 환율은 1380.00원입니다."
        }
    """
    targets = indicators if indicators else list(STAT_CODES.keys()) + [f"환율_{c}" for c in EXCHANGE_CODES]
    result = {}

    for name in targets:
        # 환율 처리
        if name.startswith("환율_"):
            currency = name.replace("환율_", "")
            if currency not in EXCHANGE_CODES:
                continue
            row = _fetch_latest("731Y001", EXCHANGE_CODES[currency], "D")
            unit = "원/100엔" if currency == "JPY" else f"원/{currency}"
        elif name in STAT_CODES:
            stat_code, item_code, cycle = STAT_CODES[name]
            row = _fetch_latest(stat_code, item_code, cycle)
            unit = _get_unit(name)
        else:
            continue

        if row:
            result[name] = {
                "value": row.get("DATA_VALUE", ""),
                "period": row.get("TIME", ""),
                "unit": unit,
            }
        else:
            result[name] = {"value": "조회 실패", "period": "", "unit": unit}

    result["summary"] = _build_summary(result)
    return result


def _get_unit(name: str) -> str:
    units = {"기준금리": "%", "CPI": "지수"}
    return units.get(name, "")


def _build_summary(result: dict) -> str:
    parts = []
    if "기준금리" in result and result["기준금리"]["value"] != "조회 실패":
        parts.append(f"현재 기준금리는 {result['기준금리']['value']}%")
    for currency in EXCHANGE_CODES:
        key = f"환율_{currency}"
        if key in result and result[key]["value"] != "조회 실패":
            parts.append(f"{key.replace('환율_', '')} 환율은 {result[key]['value']}{result[key]['unit']}")
    if "CPI" in result and result["CPI"]["value"] != "조회 실패":
        parts.append(f"소비자물가지수는 {result['CPI']['value']}")
    return "이며, ".join(parts) + "입니다." if parts else "거시경제 지표를 조회할 수 없습니다."


if __name__ == "__main__":
    data = get_macro_indicators()
    for k, v in data.items():
        if k == "summary":
            print(f"\n요약: {v}")
        else:
            print(f"{k}: {v['value']} {v['unit']} ({v['period']})")
