from typing import Literal


def calculate_tax_saving(
    annual_income: int,
    irp_amount: int = 0,
    isa_transfer_amount: int = 0,
) -> dict:
    """IRP·ISA 납입에 따른 연간 세액공제 환급 예상액을 계산합니다.

    Args:
        annual_income: 연간 총급여 또는 종합소득금액 (만 원 단위)
        irp_amount: IRP + 연금저축 합산 연간 납입액 (만 원 단위, 최대 900만 원 한도 적용)
        isa_transfer_amount: ISA 만기 금액 중 IRP로 전환한 금액 (만 원 단위)

    Returns:
        세액공제 계산 결과 dict
    """
    # 세액공제율 결정 (총급여 기준)
    if annual_income <= 5500:
        rate = 0.165  # 16.5% (소득세 15% + 지방소득세 1.5%)
    else:
        rate = 0.132  # 13.2%

    # IRP·연금저축 세액공제 한도: 900만 원
    irp_deductible = min(irp_amount, 900)
    irp_refund = round(irp_deductible * rate)

    # ISA 만기 IRP 전환 추가 공제: 전환액의 10%, 최대 300만 원
    isa_deductible = min(isa_transfer_amount, 3000)
    isa_extra_deductible = min(round(isa_deductible * 0.1), 300)
    isa_extra_refund = round(isa_extra_deductible * rate)

    total_refund = irp_refund + isa_extra_refund

    return {
        "연간_총급여": f"{annual_income}만 원",
        "세액공제율": f"{rate * 100:.1f}%",
        "IRP_납입액": f"{irp_amount}만 원",
        "IRP_공제한도_적용": f"{irp_deductible}만 원",
        "IRP_환급_예상": f"{irp_refund}만 원",
        "ISA_전환액": f"{isa_transfer_amount}만 원",
        "ISA_추가_공제액": f"{isa_extra_deductible}만 원",
        "ISA_추가_환급_예상": f"{isa_extra_refund}만 원",
        "총_환급_예상액": f"{total_refund}만 원",
        "안내": "실제 환급액은 다른 공제 항목 및 세법 개정에 따라 달라질 수 있습니다.",
    }


def calculate_maturity_amount(
    principal: int,
    annual_rate: float,
    months: int,
    product_type: Literal["예금", "적금"] = "예금",
) -> dict:
    """예금·적금 만기 수령액을 계산합니다.

    Args:
        principal: 예금은 거치 원금, 적금은 월 납입액 (만 원 단위)
        annual_rate: 연 이자율 (%, 예: 3.5)
        months: 납입 기간 (개월)
        product_type: "예금" (단리 거치) 또는 "적금" (단리 월납)

    Returns:
        만기 수령액 계산 결과 dict
    """
    r = annual_rate / 100

    if product_type == "예금":
        interest = round(principal * r * months / 12)
        total = principal + interest
        return {
            "상품": "예금",
            "거치_원금": f"{principal}만 원",
            "연이율": f"{annual_rate}%",
            "기간": f"{months}개월",
            "이자_합계": f"{interest}만 원",
            "세전_만기_수령액": f"{total}만 원",
            "안내": "이자소득세(15.4%) 적용 전 금액입니다.",
        }
    else:  # 적금 단리
        total_principal = principal * months
        # 단리 적금 이자: 월납 * 연이율/12 * (n*(n+1)/2) / n * n = 월납 * 연이율/12 * (납입월수+1)/2 * 납입월수
        interest = round(principal * (r / 12) * months * (months + 1) / 2)
        total = total_principal + interest
        return {
            "상품": "적금",
            "월_납입액": f"{principal}만 원",
            "총_납입_원금": f"{total_principal}만 원",
            "연이율": f"{annual_rate}%",
            "기간": f"{months}개월",
            "이자_합계": f"{interest}만 원",
            "세전_만기_수령액": f"{total}만 원",
            "안내": "이자소득세(15.4%) 적용 전 금액입니다.",
        }


def calculate_pension_payout(
    balance: int,
    start_age: int,
    duration_years: int,
) -> dict:
    """IRP·연금 적립금의 월 수령액 및 연간 수령액을 추정합니다.

    Args:
        balance: 연금 적립 잔액 (만 원 단위)
        start_age: 연금 수령 시작 나이
        duration_years: 수령 기간 (년, 최소 10년 권장)

    Returns:
        월·연간 수령액 추정 결과 dict
    """
    if duration_years < 1:
        return {"오류": "수령 기간은 최소 1년 이상이어야 합니다."}

    total_months = duration_years * 12
    monthly = round(balance / total_months)
    annual = monthly * 12

    # 55세 이상 연금 수령 시 연금소득세율
    if start_age < 55:
        tax_note = "연금 수령은 만 55세 이후부터 가능합니다."
        tax_rate_str = "-"
    elif start_age < 70:
        tax_rate_str = "5.5%"
        tax_note = "만 55~69세 수령 시 연금소득세 5.5% 적용."
    elif start_age < 80:
        tax_rate_str = "4.4%"
        tax_note = "만 70~79세 수령 시 연금소득세 4.4% 적용."
    else:
        tax_rate_str = "3.3%"
        tax_note = "만 80세 이상 수령 시 연금소득세 3.3% 적용."

    return {
        "적립_잔액": f"{balance}만 원",
        "수령_시작_나이": f"만 {start_age}세",
        "수령_기간": f"{duration_years}년",
        "월_수령액_추정": f"{monthly}만 원",
        "연간_수령액_추정": f"{annual}만 원",
        "연금소득세율": tax_rate_str,
        "안내": tax_note + " 실제 수령액은 운용 수익률 및 세법 변경에 따라 달라질 수 있습니다.",
    }
