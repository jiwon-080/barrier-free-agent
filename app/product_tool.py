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


def get_irp_info(investment_profile: str = "") -> dict:
    """NH농협 개인형IRP(개인형퇴직연금) 상품 정보를 반환합니다.

    Args:
        investment_profile: 사용자 투자성향. '위험회피형', '위험중립형', '위험선호형' 중 하나.
                            빈 문자열이면 일반 안내를 반환합니다.

    Returns:
        dict: 상품정보, 주요혜택, 경고사항, 투자성향진단필요, 추천다음단계 포함
    """
    irp_products = _PRODUCTS.get("irp", [])
    if not irp_products:
        return {"오류": "IRP 상품 정보를 찾을 수 없습니다."}

    p = irp_products[0]
    risk_profiles = p.get("investment_risk_profile", {})

    # 성향이 파악된 경우 해당 운용방법만 강조, 없으면 전체 표시
    if investment_profile and investment_profile in risk_profiles:
        risk_highlight = f"  - **{investment_profile}**: {risk_profiles[investment_profile]}"
        others = "\n".join(
            f"  - {k}: {v}" for k, v in risk_profiles.items() if k != investment_profile
        )
        risk_lines = risk_highlight + ("\n" + others if others else "")
    else:
        risk_lines = "\n".join(f"  - {k}: {v}" for k, v in risk_profiles.items())

    상품정보 = (
        f"## {p['fin_prdt_nm']} ({p['kor_co_nm']})\n\n"
        f"**가입대상(여유자금)**: {p.get('join_member_savings', '-')}\n"
        f"**가입대상(퇴직금)**: {p.get('join_member_retirement', '-')}\n"
        f"**연간 납입한도**: {p['annual_limit_savings']:,}원 (연금저축 합산)\n"
        f"**투자가능상품**: {p.get('investable_products', '-')}\n\n"
        f"**세액공제 혜택**\n{p.get('tax_benefit', '-')}\n"
        f"  · {p.get('tax_saving_low_income', '')}\n"
        f"  · {p.get('tax_saving_high_income', '')}\n\n"
        f"**연금수령 요건**: {p.get('pension_requirement', '-')} → {p.get('pension_period_min_years', 10)}년 이상 수령\n"
        f"**퇴직소득세 절세**: {p.get('retirement_tax_pension', '-')}\n\n"
        f"**투자성향별 운용방법**\n{risk_lines}\n\n"
        f"**예금자보호**: {p.get('deposit_protection', '-')}\n"
        f"**특이사항**: {p.get('spcl_cnd', '-')}\n"
        f"**유의사항**: {p.get('etc_note', '-')}"
    )

    # 성향별 경고사항 / 추천다음단계 분기
    if investment_profile == "위험회피형":
        경고사항 = [
            "원금 손실 위험 있는 투자 상품은 가입 전 반드시 투자성향 진단 필요",
            "만 55세 이상·가입기간 5년 이상 충족해야 연금 수령 가능",
            "중도해지 시 기타소득세(16.5%) 부과 및 세액공제 혜택 전액 반환",
        ]
        추천다음단계 = [
            {"label": "투자성향 진단 받기", "route": "investment_diagnosis"},
            {"label": "IRP 신규가입 화면", "route": "irp_new"},
        ]
        진단필요 = True
    elif investment_profile == "위험선호형":
        경고사항 = [
            "투자 상품 포함 시 원금 손실 발생 가능 — 공격적 운용 시 손실 폭 클 수 있음",
            "만 55세 이상·가입기간 5년 이상 충족해야 연금 수령 가능",
            "중도해지 시 기타소득세(16.5%) 부과 및 세액공제 혜택 전액 반환",
        ]
        추천다음단계 = [
            {"label": "IRP 신규가입 화면", "route": "irp_new"},
            {"label": "포트폴리오 현황", "route": "portfolio"},
        ]
        진단필요 = False
    else:  # 위험중립형 or 미파악
        경고사항 = [
            "만 55세 이상·가입기간 5년 이상 충족해야 연금 수령 가능",
            "중도해지 시 기타소득세(16.5%) 부과 및 세액공제 혜택 전액 반환",
            "투자 상품 포함 시 원금 손실 발생 가능",
        ]
        추천다음단계 = [
            {"label": "투자성향 진단 받기", "route": "investment_diagnosis"},
            {"label": "IRP 신규가입 화면", "route": "irp_new"},
        ]
        진단필요 = True

    return {
        "상품정보": 상품정보,
        "주요혜택": f"연 {p['annual_limit_savings'] // 10000}백만 원까지 세액공제, 연금 수령 시 퇴직소득세 절감",
        "경고사항": 경고사항,
        "투자성향진단필요": 진단필요,
        "추천다음단계": 추천다음단계,
    }


def get_isa_info(isa_type: str = "전체", investment_profile: str = "") -> dict:
    """NH농협 ISA(개인종합자산관리계좌) 상품 정보를 반환합니다.

    Args:
        isa_type: "신탁형", "일임형", "전체" 중 하나 (기본값: "전체")
        investment_profile: 사용자 투자성향. '위험회피형', '위험중립형', '위험선호형' 중 하나.
                            빈 문자열이면 일반 안내를 반환합니다.

    Returns:
        dict: 상품정보, 주요혜택, 경고사항, 투자성향진단필요, 추천다음단계 포함
    """
    isa_products = _PRODUCTS.get("isa", [])
    if not isa_products:
        return {"오류": "ISA 상품 정보를 찾을 수 없습니다."}

    if isa_type in ("신탁형", "일임형"):
        targets = [p for p in isa_products if p.get("isa_type") == isa_type]
    else:
        targets = isa_products

    if not targets:
        return {"오류": f"'{isa_type}' ISA 상품 정보를 찾을 수 없습니다."}

    lines = ["## NH농협 ISA(개인종합자산관리계좌) 안내\n"]
    for p in targets:
        lines.append(f"### {p['fin_prdt_nm']}")
        lines.append(f"**유형**: {p.get('isa_type', '-')}  |  **원금보장**: {'보장' if p.get('principal_protected') else '비보장'}")
        lines.append(f"**가입대상**: {p.get('join_member', '-')}")
        lines.append(f"**가입제한**: {p.get('join_deny', '-')}")
        lines.append(f"**납입한도**: 연간 {p['annual_limit']:,}원 / 총 {p['total_limit']:,}원")
        lines.append(f"**의무가입기간**: {p.get('min_period_years', 3)}년")
        lines.append(f"**투자가능상품**: {p.get('investable_products', '-')}")
        lines.append(f"**세제혜택(일반)**: {p.get('tax_benefit_general', '-')}")
        lines.append(f"**세제혜택(우대)**: {p.get('tax_benefit_priority', '-')}")
        if "model_portfolios" in p:
            lines.append("**모델포트폴리오(수수료)**:")
            for mp in p["model_portfolios"]:
                lines.append(f"  - {mp['name']}: 연 {mp['annual_fee_rate_pct']}%")
            lines.append(f"  ({p.get('fee_note', '')})")
        else:
            lines.append(f"**수수료**: {p.get('fee', '-')}")
        lines.append(f"**특징**: {p.get('spcl_cnd', '-')}")
        lines.append(f"**유의사항**: {p.get('etc_note', '-')}\n")

    has_investment = any(
        "펀드" in p.get("investable_products", "") or "ETF" in p.get("investable_products", "")
        for p in targets
    )

    # 성향별 경고사항 / 추천다음단계 분기
    if investment_profile == "위험회피형":
        경고사항 = [
            "의무가입기간 3년 — 중도 해지 시 세금 혜택 전액 소멸",
            "납입원금 범위 내 부분 인출만 가능하며 인출 후 재납입 불가",
            "원금 손실 위험이 없는 예·적금 위주 신탁형을 권장합니다",
        ]
        추천다음단계 = [
            {"label": "투자성향 진단 받기", "route": "investment_diagnosis"},
            {"label": "ISA 신탁형 가입", "route": "financial_products/isa"},
        ]
        진단필요 = has_investment
    elif investment_profile == "위험선호형":
        경고사항 = [
            "의무가입기간 3년 — 중도 해지 시 세금 혜택 전액 소멸",
            "납입원금 범위 내 부분 인출만 가능하며 인출 후 재납입 불가",
            "일임형 선택 시 펀드·ETF 포함으로 원금 손실 발생 가능",
        ]
        추천다음단계 = [
            {"label": "ISA 일임형 가입", "route": "financial_products/isa"},
            {"label": "투자성향 진단 받기", "route": "investment_diagnosis"},
        ]
        진단필요 = has_investment
    else:  # 위험중립형 or 미파악
        경고사항 = [
            "의무가입기간 3년 — 중도 해지 시 세금 혜택 전액 소멸",
            "납입원금 범위 내 부분 인출만 가능하며 인출 후 재납입 불가 (입출금 자유 아님)",
            "신탁형 선택 시 투자 상품 포함으로 원금 손실 발생 가능",
        ]
        추천다음단계 = [
            {"label": "투자성향 진단 먼저 받기", "route": "investment_diagnosis"},
            {"label": "ISA 가입 화면으로 이동", "route": "financial_products/isa"},
        ]
        진단필요 = has_investment

    return {
        "상품정보": "\n".join(lines),
        "주요혜택": "일반형 기준 이익금 200만 원까지 비과세 (서민형·농어민형은 400만 원). 비과세 한도 초과분은 9.9% 분리과세.",
        "경고사항": 경고사항,
        "투자성향진단필요": 진단필요,
        "추천다음단계": 추천다음단계,
    }


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
