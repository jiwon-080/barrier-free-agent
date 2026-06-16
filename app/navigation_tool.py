def navigate_ui(screen_name: str) -> dict:
    """고령층 사용자를 위해 목적지 화면의 route와 음성 안내를 반환합니다.
    에이전트가 동의를 구한 후 해당 route로 직접 이동합니다.

    Args:
        screen_name: 이동하고자 하는 화면 또는 기능 설명
                     (예: '예금', '적금', '펀드', 'ISA', '퇴직연금', '이체' 등)

    Returns:
        type='navigation' : route, consent_message, voice_guide, highlight_target
        type='error'      : 알 수 없는 요청
    """
    # ── 실제 NH농협 앱 메뉴 구조 기반 ──────────────────────────────────────
    # 금융상품 탭: 입출금/예금/적금/주택청약/펀드/대출/외환/퇴직연금/신탁/ISA/보험/골드실버
    # 사이드 메뉴: 조회, 이체/출금, 가입상품관리, 금융상품, 외환, 퇴직연금, 공과금/채권, 내자산

    navigation_map = {
        # ── 금융상품 ────────────────────────────────────────────────────────
        "입출금": {
            "route": "financial_products/demand_deposit",
            "consent_message": "입출금 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "입출금 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "입출금",
        },
        "예금": {
            "route": "financial_products/deposit",
            "consent_message": "예금 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "예금 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "예금",
        },
        "적금": {
            "route": "financial_products/saving",
            "consent_message": "적금 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "적금 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "적금",
        },
        "주택청약": {
            "route": "financial_products/housing_subscription",
            "consent_message": "주택청약 화면으로 이동해 드릴까요?",
            "voice_guide": "주택청약 화면으로 안내해 드릴게요.",
            "highlight_target": "주택청약",
        },
        "펀드": {
            "route": "financial_products/fund",
            "consent_message": "펀드 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "펀드 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "펀드",
        },
        "투자자성향": {
            "route": "investment_diagnosis",
            "consent_message": "투자자 성향 진단 화면으로 이동해 드릴까요?",
            "voice_guide": "펀드 가입 전에 투자자 성향 진단을 먼저 받으셔야 합니다. 진단 화면으로 안내해 드릴게요.",
            "highlight_target": "투자자성향진단",
        },
        "ETF": {
            "route": "financial_products/fund/trust/etf",
            "consent_message": "ETF 화면으로 이동해 드릴까요?",
            "voice_guide": "ETF는 펀드 메뉴 안 신탁에 있어요. 해당 화면으로 안내해 드릴게요.",
            "highlight_target": "ETF",
        },
        "대출": {
            "route": "financial_products/loan",
            "consent_message": "대출 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "대출 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "대출",
        },
        "외환": {
            "route": "financial_products/foreign_exchange",
            "consent_message": "외환 화면으로 이동해 드릴까요?",
            "voice_guide": "외환 화면으로 안내해 드릴게요.",
            "highlight_target": "외환",
        },
        "퇴직연금": {
            "route": "financial_products/retirement_pension",
            "consent_message": "퇴직연금 화면으로 이동해 드릴까요?",
            "voice_guide": "퇴직연금 화면으로 안내해 드릴게요.",
            "highlight_target": "퇴직연금",
        },
        "신탁": {
            "route": "financial_products/trust",
            "consent_message": "신탁 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "신탁 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "신탁",
        },
        "ISA": {
            "route": "financial_products/isa",
            "consent_message": "ISA 화면으로 이동해 드릴까요?",
            "voice_guide": "ISA 화면으로 안내해 드릴게요.",
            "highlight_target": "ISA",
        },
        "보험": {
            "route": "financial_products/insurance",
            "consent_message": "보험 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "보험 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "보험",
        },
        "골드": {
            "route": "financial_products/gold_silver",
            "consent_message": "골드/실버 상품 화면으로 이동해 드릴까요?",
            "voice_guide": "골드/실버 상품 화면으로 안내해 드릴게요.",
            "highlight_target": "골드/실버",
        },
        "금융상품비교": {
            "route": "financial_products/comparison",
            "consent_message": "금융상품비교 화면으로 이동해 드릴까요?",
            "voice_guide": "금융상품비교 화면으로 안내해 드릴게요.",
            "highlight_target": "금융상품비교",
        },
        # ── 가입상품관리 ─────────────────────────────────────────────────────
        "가입상품관리": {
            "route": "my_products",
            "consent_message": "가입상품관리 화면으로 이동해 드릴까요?",
            "voice_guide": "내가 가입한 상품을 한눈에 볼 수 있는 화면으로 안내해 드릴게요.",
            "highlight_target": "가입상품관리",
        },
        "내계좌": {
            "route": "my_products/account",
            "consent_message": "내 계좌 목록 화면으로 이동해 드릴까요?",
            "voice_guide": "내 계좌 목록 화면으로 안내해 드릴게요.",
            "highlight_target": "계좌",
        },
        # ── 조회/이체 ────────────────────────────────────────────────────────
        "전체계좌조회": {
            "route": "inquiry/all_accounts",
            "consent_message": "전체 계좌 조회 화면으로 이동해 드릴까요?",
            "voice_guide": "전체 계좌 조회 화면으로 안내해 드릴게요.",
            "highlight_target": "전체계좌조회",
        },
        "거래내역": {
            "route": "inquiry/transaction_history",
            "consent_message": "거래내역 화면으로 이동해 드릴까요?",
            "voice_guide": "거래내역 화면으로 안내해 드릴게요.",
            "highlight_target": "거래내역",
        },
        "이체": {
            "route": "transfer/account",
            "consent_message": "계좌이체 화면으로 이동해 드릴까요?",
            "voice_guide": "계좌이체 화면으로 안내해 드릴게요.",
            "highlight_target": "계좌이체",
        },
        "ATM": {
            "route": "transfer/atm",
            "consent_message": "ATM 출금 화면으로 이동해 드릴까요?",
            "voice_guide": "ATM 출금 화면으로 안내해 드릴게요.",
            "highlight_target": "ATM 출금",
        },
        # ── 기타 ─────────────────────────────────────────────────────────────
        "내자산": {
            "route": "my_assets",
            "consent_message": "내 자산 현황 화면으로 이동해 드릴까요?",
            "voice_guide": "내 자산 현황 화면으로 안내해 드릴게요.",
            "highlight_target": "내 자산",
        },
        "공과금": {
            "route": "utility_bill",
            "consent_message": "공과금/채권 화면으로 이동해 드릴까요?",
            "voice_guide": "공과금/채권 화면으로 안내해 드릴게요.",
            "highlight_target": "공과금/채권",
        },
        "큰글": {
            "route": "settings/bigtext_mode",
            "consent_message": "큰글 모드 화면으로 이동해 드릴까요?",
            "voice_guide": "글자를 크게 볼 수 있는 큰글 모드 화면으로 안내해 드릴게요.",
            "highlight_target": "큰글도우미",
        },
        "고객센터": {
            "route": "customer_service",
            "consent_message": "고객센터 화면으로 이동해 드릴까요?",
            "voice_guide": "고객센터 화면으로 안내해 드릴게요.",
            "highlight_target": "고객센터",
        },
    }

    upper = screen_name.upper()

    # 투자성향 진단 (IRP보다 먼저 체크 — "투자성향 진단" 키워드가 IRP 블록으로 넘어가지 않도록)
    _DIAGNOSIS_KEYWORDS = ["투자성향", "투자자성향", "성향진단", "성향 진단", "위험성향", "투자 성향"]
    if any(kw in screen_name for kw in _DIAGNOSIS_KEYWORDS):
        return {
            "type": "navigation",
            "route": "investment_diagnosis",
            "consent_message": "투자성향 진단 화면으로 이동해 드릴까요?",
            "voice_guide": "투자성향 진단 화면으로 안내해 드릴게요.",
            "highlight_target": "투자자성향진단",
        }

    # MY퇴직연금 / 내 퇴직연금 (IRP 이전에 체크)
    if "MY퇴직" in upper or "내퇴직" in upper or "내 퇴직" in screen_name:
        return {
            "type": "navigation",
            "route": "my_pension",
            "consent_message": "MY 퇴직연금 화면으로 이동해 드릴까요?",
            "voice_guide": "MY 퇴직연금 현황 화면으로 안내해 드릴게요.",
            "highlight_target": "MY퇴직연금",
        }

    # IRP — 의도에 따라 구체적 화면으로 분기
    if "IRP" in upper:
        signup_keywords = ["신규", "가입", "만들", "개설", "시작"]
        tax_keywords = ["세액공제", "세금", "절세"]
        _IRP_STEPS = [
            {"route": "irp_new", "highlight": "개인형 IRP 세액공제용", "instruction": "개인형 IRP 세액공제용을 선택해주세요"},
            {"route": "irp_tax_saving", "highlight": "가입확인", "instruction": "가입 전 필수 항목을 확인해주세요"},
        ]
        if any(kw in screen_name for kw in signup_keywords):
            return {
                "type": "navigation",
                "route": "irp_new",
                "consent_message": "IRP 신규가입 화면으로 안내해 드릴까요?",
                "voice_guide": "IRP 신규가입 화면으로 안내해 드릴게요.",
                "highlight_target": "IRP",
                "steps": _IRP_STEPS,
            }
        if any(kw in screen_name for kw in tax_keywords):
            return {
                "type": "navigation",
                "route": "irp_tax_saving",
                "consent_message": "IRP 세액공제 가입 화면으로 안내해 드릴까요?",
                "voice_guide": "IRP 세액공제 가입 화면으로 안내해 드릴게요.",
                "highlight_target": "IRP",
                "steps": _IRP_STEPS,
            }
        # 일반 IRP 조회 → 퇴직연금 카테고리
        nav = navigation_map["퇴직연금"].copy()
        nav["voice_guide"] = "IRP는 퇴직연금 메뉴 안에 있습니다. 퇴직연금 화면으로 안내해 드릴게요."
        nav["steps"] = [
            {"route": "retirement_pension", "highlight": "IRP 신규가입/입금", "instruction": "IRP 신규가입/입금을 선택해주세요"},
        ]
        return {"type": "navigation", **nav}

    # ISA 가입 의도
    if "ISA" in upper:
        signup_keywords = ["신규", "가입", "만들", "개설", "시작"]
        if any(kw in screen_name for kw in signup_keywords):
            return {
                "type": "navigation",
                "route": "financial_products/isa",
                "consent_message": "ISA 가입 화면으로 안내해 드릴까요?",
                "voice_guide": "ISA 가입 화면으로 안내해 드릴게요.",
                "highlight_target": "ISA가입",
            }

    # 키워드 매칭
    for key, nav_info in navigation_map.items():
        if key in screen_name or key.upper() in upper:
            return {"type": "navigation", **nav_info}

    return {
        "type": "error",
        "voice_guide": (
            f"죄송해요, '{screen_name}'에 대한 화면을 찾지 못했어요. "
            "'예금', '적금', '이체', '퇴직연금'처럼 말씀해 주시겠어요?"
        ),
    }
