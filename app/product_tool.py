import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
PRODUCT_PATH = BASE_DIR / "data" / "rag" / "fss_product.json"

# join_deny 코드 → 사람이 읽을 수 있는 텍스트
_JOIN_DENY_MAP = {"1": "제한없음", "2": "서민전용", "3": "일부제한"}

# FSS 데이터상 NH농협 공식 명칭
_NH_COMPANY_NAME = "농협은행주식회사"

# 카테고리 키 매핑
_CATEGORY_MAP = {
    ("예금", "은행"):     "deposit_bank",
    ("예금", "저축은행"): "deposit_save",
    ("적금", "은행"):     "saving_bank",
    ("적금", "저축은행"): "saving_save",
}


def _load_products() -> dict:
    try:
        with open(PRODUCT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


_PRODUCTS = _load_products()


def _best_rate_for_term(options: list, term_months: Optional[int]) -> Optional[float]:
    """특정 기간의 최고금리 반환. term_months=None 이면 전 기간 최고금리."""
    candidates = [
        opt["intr_rate2"]
        for opt in options
        if term_months is None or str(opt.get("save_trm", "")) == str(term_months)
    ]
    return max(candidates) if candidates else None


def _format_options(options: list) -> str:
    lines = []
    for opt in sorted(options, key=lambda o: int(o.get("save_trm", 0))):
        trm   = opt.get("save_trm", "?")
        base  = opt.get("intr_rate", "-")
        best  = opt.get("intr_rate2", "-")
        itype = opt.get("intr_rate_type_nm", "")
        lines.append(f"  {trm}개월({itype}): 기본 {base}% / 최고 {best}%")
    return "\n".join(lines)


def search_products(
    product_type: str,
    term_months: Optional[int] = None,
    bank_type: str = "전체",
    company_filter: str = "NH농협",
    top_n: int = 5,
) -> str:
    """예금 또는 적금 상품을 금리 높은 순으로 조회합니다.

    Args:
        product_type:   "예금" 또는 "적금"
        term_months:    조회할 가입 기간(개월). 예) 12 → 12개월 상품만. None이면 전 기간.
        bank_type:      "은행", "저축은행", "전체" 중 하나 (기본값: "전체")
        company_filter: "NH농협"(기본) 또는 "전체". "전체"이면 타행 상품도 포함하여 비교.
        top_n:          반환할 상품 수 (기본값: 5)

    Returns:
        상위 N개 상품 요약 문자열
    """
    if product_type not in ("예금", "적금"):
        return "product_type은 '예금' 또는 '적금'만 입력 가능합니다."

    # 조회 대상 카테고리 결정
    if bank_type == "전체":
        keys = [v for (pt, _), v in _CATEGORY_MAP.items() if pt == product_type]
    elif bank_type in ("은행", "저축은행"):
        key = _CATEGORY_MAP.get((product_type, bank_type))
        keys = [key] if key else []
    else:
        return "bank_type은 '은행', '저축은행', '전체' 중 하나를 입력해 주세요."

    # 상품 수집 + 회사 필터 + 해당 기간 최고금리 계산
    candidates = []
    for key in keys:
        for prod in _PRODUCTS.get(key, []):
            if company_filter == "NH농협" and prod["kor_co_nm"] != _NH_COMPANY_NAME:
                continue
            rate = _best_rate_for_term(prod.get("options", []), term_months)
            if rate is None:
                continue
            candidates.append({
                "kor_co_nm":   prod["kor_co_nm"],
                "fin_prdt_nm": prod["fin_prdt_nm"],
                "best_rate":   rate,
                "join_member": prod.get("join_member", ""),
                "join_deny":   _JOIN_DENY_MAP.get(str(prod.get("join_deny", "1")), ""),
                "join_way":    prod.get("join_way", ""),
            })

    if not candidates:
        period_txt = f"{term_months}개월 " if term_months else ""
        filter_txt = "NH농협" if company_filter == "NH농협" else ""
        return f"{filter_txt} {period_txt}{product_type} 상품을 찾을 수 없습니다."

    # 금리 내림차순 정렬 후 상위 N개
    top = sorted(candidates, key=lambda x: x["best_rate"], reverse=True)[:top_n]

    period_txt  = f"{term_months}개월 " if term_months else ""
    filter_txt  = "NH농협 " if company_filter == "NH농협" else "전체 은행 "
    header = f"## {filter_txt}{period_txt}{product_type} 금리 TOP {len(top)}\n"
    lines = []
    for i, p in enumerate(top, 1):
        lines.append(
            f"{i}. [{p['kor_co_nm']}] {p['fin_prdt_nm']}\n"
            f"   최고금리: {p['best_rate']}%  |  가입대상: {p['join_member']}  |  {p['join_deny']}\n"
            f"   가입방법: {p['join_way']}"
        )
    return header + "\n\n".join(lines)


def get_product_detail(product_name: str) -> str:
    """특정 금융 상품의 상세 정보(전 기간 금리표, 우대조건, 유의사항)를 반환합니다.

    Args:
        product_name: 상품명 (부분 일치 검색 가능). 예) "WON플러스예금"

    Returns:
        상품 상세 정보 문자열
    """
    all_products = []
    for items in _PRODUCTS.values():
        all_products.extend(items)

    nh_products = [p for p in all_products if p["kor_co_nm"] == _NH_COMPANY_NAME]

    # NH농협 내에서 정확 일치 → 부분 일치 → 전체에서 부분 일치 순으로 탐색
    match = (
        next((p for p in nh_products if p["fin_prdt_nm"] == product_name), None)
        or next((p for p in nh_products if product_name in p["fin_prdt_nm"]), None)
        or next((p for p in all_products if product_name in p["fin_prdt_nm"]), None)
    )

    if not match:
        return f"'{product_name}' 상품을 찾을 수 없습니다. 상품명을 다시 확인해 주세요."

    join_deny = _JOIN_DENY_MAP.get(str(match.get("join_deny", "1")), "")
    options_str = _format_options(match.get("options", []))
    spcl = match.get("spcl_cnd") or "없음"
    note = match.get("etc_note") or "없음"
    limit = match.get("max_limit")
    limit_str = f"{limit:,}원" if limit else "제한없음"

    return (
        f"## {match['fin_prdt_nm']} ({match['kor_co_nm']})\n\n"
        f"**가입대상**: {match.get('join_member', '-')}  ({join_deny})\n"
        f"**가입방법**: {match.get('join_way', '-')}\n"
        f"**최대한도**: {limit_str}\n\n"
        f"**금리 안내 (기본금리 / 최고금리)**\n{options_str}\n\n"
        f"**우대조건**\n{spcl}\n\n"
        f"**유의사항**\n{note}"
    )


def compare_products(product_names: list[str]) -> str:
    """여러 상품을 나란히 비교합니다 (최고금리 기준).

    Args:
        product_names: 비교할 상품명 목록 (최대 3개 권장)

    Returns:
        비교표 문자열
    """
    all_products = []
    for items in _PRODUCTS.values():
        all_products.extend(items)

    results = []
    for name in product_names:
        match = next((p for p in all_products if name in p["fin_prdt_nm"]), None)
        if match:
            best = _best_rate_for_term(match.get("options", []), None)
            results.append({
                "name":    match["fin_prdt_nm"],
                "company": match["kor_co_nm"],
                "best":    best,
                "member":  match.get("join_member", "-"),
                "way":     match.get("join_way", "-"),
            })
        else:
            results.append({"name": name, "company": "?", "best": None,
                             "member": "-", "way": "-"})

    lines = ["## 상품 비교", ""]
    for r in results:
        rate_str = f"{r['best']}%" if r["best"] is not None else "정보없음"
        lines.append(
            f"### {r['name']} ({r['company']})\n"
            f"- 최고금리: {rate_str}\n"
            f"- 가입대상: {r['member']}\n"
            f"- 가입방법: {r['way']}"
        )
    return "\n\n".join(lines)
