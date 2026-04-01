def navigate_ui(screen_name: str) -> dict:
    """노년층 사용자를 위해 목적지 화면의 route와 음성 안내를 반환합니다.
    에이전트가 동의를 구한 후 해당 route로 직접 이동합니다.

    Args:
        screen_name: 이동하고자 하는 화면 또는 기능 설명 (예: 'IRP 가입', 'MY퇴직연금', 'ETF')

    Returns:
        type='navigation' : route, consent_message, voice_guide, highlight_target
        status='hold'     : 고위험 상품 — 투자 성향 진단 유도
        type='suggestion' : 추가 맥락 필요 (예: IRP 내 예금 운용)
        type='error'      : 알 수 없는 요청
    """
    upper = screen_name.upper()

    # ── 1. 고위험 상품 → hold (의도된 마찰) ────────────────────────────────
    if "ETF" in upper or "펀드" in screen_name or "FUND" in upper:
        return {
            "status": "hold",
            "routing": "투자 성향 진단 메뉴",
            "route": "investment_diagnosis",
            "voice_guide": (
                "ETF나 펀드는 원금 손실 위험이 있는 고위험 상품이에요. "
                "바로 가입하시기 전에 투자 성향 진단을 먼저 받아보셔야 해요. "
                "진단 화면으로 이동해 드릴까요?"
            ),
            "highlight_target": "투자 성향 진단",
        }

    # ── 2. 직접 이동 가능한 주요 화면 ──────────────────────────────────────
    navigation_map = {
        "IRP": {
            "type": "navigation",
            "route": "irp_tax_saving",
            "consent_message": "IRP 세액공제용 가입 화면으로 바로 이동해 드릴까요?",
            "voice_guide": (
                "IRP 가입 화면으로 안내해 드릴게요. "
                "원래는 금융상품 → 퇴직연금 → IRP 신규가입 순으로 4단계를 직접 눌러야 하는데, "
                "제가 한 번에 이동해 드릴게요."
            ),
            "highlight_target": "개인형 IRP 세액공제용",
        },
        "MY퇴직연금": {
            "type": "navigation",
            "route": "my_pension",
            "consent_message": "내 퇴직연금 현황 화면으로 바로 이동해 드릴까요?",
            "voice_guide": "내 연금 현황 화면으로 이동해 드릴게요.",
            "highlight_target": "MY퇴직연금",
        },
        "포트폴리오": {
            "type": "navigation",
            "route": "portfolio",
            "consent_message": "포트폴리오 화면으로 바로 이동해 드릴까요?",
            "voice_guide": "포트폴리오 화면으로 이동해 드릴게요.",
            "highlight_target": "포트폴리오",
        },
        "연금설계": {
            "type": "navigation",
            "route": "pension_design",
            "consent_message": "연금설계 화면으로 바로 이동해 드릴까요?",
            "voice_guide": "연금설계 화면으로 이동해 드릴게요.",
            "highlight_target": "연금설계",
        },
    }

    for key, nav_info in navigation_map.items():
        if key in screen_name or key in upper:
            return nav_info

    # ── 3. IRP 내 운용상품(예금 등) → suggestion ────────────────────────────
    if "예금" in screen_name or "적금" in screen_name:
        return {
            "type": "suggestion",
            "voice_guide": (
                "예금 상품은 IRP 계좌 안에서 운용하는 방식이에요. "
                "IRP 계좌가 있으시면 바로 운용 상품 화면으로 안내해 드릴게요. "
                "혹시 IRP 계좌가 없으신가요?"
            ),
        }

    # ── 4. 알 수 없는 요청 ──────────────────────────────────────────────────
    return {
        "type": "error",
        "voice_guide": (
            f"죄송해요, '{screen_name}'에 대한 화면을 찾지 못했어요. "
            "'IRP 가입'이나 '내 연금 현황'처럼 말씀해 주시겠어요?"
        ),
    }
