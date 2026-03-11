from google.adk.tools import tool

@tool
def navigate_ui(user_intent: str) -> dict:
    """
    사용자의 의도에 따라 NH농협 올원뱅크의 메뉴 경로와 배리어프리 안내를 제공합니다.
    """
    # nh_menu_analysis.md의 분석 결과를 바탕으로 데이터 구성
    return {
        "menu_path": ["금융상품", "퇴직연금", "IRP 신규가입/입금"], # 시스템 경로
        "visual_guide": {
            "target_button": "금융상품",
            "location": "하단 네비게이션 바 첫 번째",
            "color": "초록색/파란색"
        },
        "voice_script": "어르신, 화면 맨 아래쪽에 있는 '금융상품'이라고 써진 글자를 눌러주시겠어요? 거기서 퇴직연금을 찾으실 수 있습니다."
    }
