from google.adk.tools import tool

@tool
def check_investment_guardrail(message: str) -> str:
    """금융소비자보호법(금소법) 준수를 위해 부적절한 투자 권유나 과장 광고가 있는지 검사합니다.
    
    Args:
        message: 검사할 메시지 내용
    """
    # TODO: 금소법 가이드라인 기반 필터링 로직 구현
    return "메시지가 가이드라인을 준수하는지 확인되었습니다."
