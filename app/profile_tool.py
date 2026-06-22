# app/profile_tool.py
from google.adk.tools.tool_context import ToolContext


def set_user_profile(
    tool_context: ToolContext,
    investment_profile: str = "",
    literacy_level: str = "",
) -> dict:
    """사용자의 투자성향 또는 금융이해도를 세션에 기록합니다.
    사용자가 투자 성향이나 금융 지식 수준을 언급할 때 호출하세요.

    Args:
        investment_profile: 투자성향 유형 (금융소비자보호법 기준).
            '위험회피형', '위험중립형', '위험선호형' 중 하나. 변경 없으면 빈 문자열.
        literacy_level: 금융이해도 수준.
            '기초', '일반', '전문가' 중 하나. 변경 없으면 빈 문자열.
    """
    recorded = {}
    if investment_profile:
        tool_context.state["user:investment_profile"] = investment_profile
        recorded["investment_profile"] = investment_profile
    if literacy_level:
        tool_context.state["user:literacy_level"] = literacy_level
        recorded["literacy_level"] = literacy_level
    return {"status": "saved", "recorded": recorded}
