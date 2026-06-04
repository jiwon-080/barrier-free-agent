# app/callbacks.py
from pathlib import Path
from google.adk.agents.callback_context import CallbackContext
from .user_memory import load_user_memory, save_user_memory


def _load_knowledge(domain: str) -> str:
    """data/knowledge/<domain>/*.md 파일을 모두 읽어 하나의 문자열로 반환."""
    knowledge_dir = Path(__file__).parent.parent / "data" / "knowledge" / domain
    pages = sorted(knowledge_dir.glob("*.md"))
    return "\n\n---\n\n".join(p.read_text(encoding="utf-8") for p in pages)


_SESSION_MEMORY_LOADED = "user:_memory_loaded"


def _after_tool_callback(tool, args, tool_context: CallbackContext, tool_response):
    tool_name = getattr(tool, "name", "")
    interests: list = list(tool_context.state.get("user:product_interests") or [])

    tag = None
    if tool_name == "get_irp_info":
        tag = "IRP"
    elif tool_name == "get_isa_info":
        tag = "ISA"
    elif tool_name == "search_products":
        pt = (args or {}).get("product_type", "")
        if pt:
            tag = pt
    elif tool_name == "navigate_ui":
        screen = (args or {}).get("screen_name", "").upper()
        for kw, label in [
            ("IRP", "IRP"), ("ISA", "ISA"), ("퇴직연금", "퇴직연금"),
            ("예금", "예금"), ("적금", "적금"), ("ETF", "ETF"),
        ]:
            if kw in screen:
                tag = label
                break

    if tag and tag not in interests:
        interests.append(tag)
        tool_context.state["user:product_interests"] = interests

    return tool_response


def _before_agent_callback(callback_context: CallbackContext):
    if not callback_context.state.get(_SESSION_MEMORY_LOADED):
        user_id = callback_context.user_id
        mem = load_user_memory(user_id)
        if mem.get("investment_profile") and not callback_context.state.get("user:investment_profile"):
            callback_context.state["user:investment_profile"] = mem["investment_profile"]
        if mem.get("literacy_level") and not callback_context.state.get("user:literacy_level"):
            callback_context.state["user:literacy_level"] = mem["literacy_level"]
        if mem.get("product_interests") and not callback_context.state.get("user:product_interests"):
            callback_context.state["user:product_interests"] = mem["product_interests"]
        callback_context.state[_SESSION_MEMORY_LOADED] = True

    interests = list(callback_context.state.get("user:product_interests") or [])
    profile = callback_context.state.get("user:investment_profile") or ""
    literacy = callback_context.state.get("user:literacy_level") or ""

    lines = []
    if profile:
        lines.append(f"- 투자성향: {profile}")
    if literacy:
        lines.append(f"- 금융이해도: {literacy}")
    if interests:
        lines.append(f"- 관심 상품: {', '.join(interests)}")

    callback_context.state["user_profile_summary"] = (
        "\n".join(lines) if lines else "파악된 정보 없음"
    )
    return None


def _after_agent_callback(callback_context: CallbackContext):
    if callback_context.state.get("user:memory_consent") == "declined":
        return None

    user_id = callback_context.user_id
    profile = callback_context.state.get("user:investment_profile") or ""
    literacy = callback_context.state.get("user:literacy_level") or ""
    interests = list(callback_context.state.get("user:product_interests") or [])

    if profile or literacy:
        save_user_memory(user_id, {
            "investment_profile": profile,
            "literacy_level": literacy,
            "product_interests": interests,
        })
    return None
