from google.adk.tools import tool

@tool
def navigate_ui(screen_name: str) -> str:
    """노년층 사용자를 위해 특정 화면으로 이동하는 방법을 안내하거나 이동합니다.
    
    Args:
        screen_name: 이동하고자 하는 화면 이름 (예: '송금', '잔액 조회', '상품 가입')
    """
    # TODO: 실제 화면 이동 로직 또는 안내 텍스트 반환 구현
    return f"'{screen_name}' 화면으로 이동하는 방법을 안내합니다."
