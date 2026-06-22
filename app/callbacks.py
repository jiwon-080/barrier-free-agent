# app/callbacks.py
import json
from pathlib import Path

from google.adk.agents.callback_context import CallbackContext
from google import genai
from google.genai import types as genai_types

from .user_memory import load_user_memory, save_user_memory
from .skill_memory import load_agent_skills


# ── 지식베이스 로더 ───────────────────────────────────────────────────────────
def _load_knowledge(domain: str) -> str:
    """data/knowledge/<domain>/*.md 파일을 모두 읽어 하나의 문자열로 반환."""
    knowledge_dir = Path(__file__).parent.parent / "data" / "knowledge" / domain
    pages = sorted(knowledge_dir.glob("*.md"))
    return "\n\n---\n\n".join(p.read_text(encoding="utf-8") for p in pages)


# ── 페르소나 라우팅 ───────────────────────────────────────────────────────────
_FEWSHOT_FILE = Path(__file__).parent.parent / "data" / "personas" / "few_shot_examples.json"

def _build_fewshot_block() -> str:
    """페르소나별 퓨샷 예시 블록을 모듈 로드 시 1회 구성."""
    if not _FEWSHOT_FILE.exists():
        return ""
    examples: list[dict] = json.loads(_FEWSHOT_FILE.read_text(encoding="utf-8"))
    by_persona: dict[str, list[str]] = {}
    for ex in examples:
        p = ex.get("persona", "")
        if p:
            by_persona.setdefault(p, []).append(ex.get("title", ""))
    lines = []
    for persona, titles in by_persona.items():
        lines.append(f"[{persona}]")
        for t in titles:
            lines.append(f"  - {t}")
    return "\n".join(lines)

_FEWSHOT_BLOCK = _build_fewshot_block()

_PERSONA_ROUTING_PROMPT = """\
아래 퓨샷 예시를 참고해, 사용자 발화가 어떤 페르소나에 가장 가까운지 판단하세요.

페르소나 기준:
- 고령층: 60대 이상. 연금·은퇴·손주 언급, 맞춤법 어색하거나 짧은 구어체.
- 사회초년생: 20대 초중반. 알바·청년 상품·주린이·처음이라는 표현.
- 주부: 남편·배우자·아이 중심. 가계 담당 여성 관점의 질문.
- 직장인: 20~30대 근로자. 연말정산·퇴직금·월급·4대보험 언급.
- 중장년: 40~50대. 노후 준비 시작, 보험 점검, 은퇴 준비 언급.

퓨샷 예시:
{fewshot_block}

사용자 발화:
"{user_message}"

위 발화의 페르소나를 다음 선택지 중 하나만 답하세요.
어떤 페르소나에도 명확히 속하지 않으면 "모름"으로 답하세요.
선택지: 고령층 / 사회초년생 / 주부 / 직장인 / 중장년 / 모름

답변 (선택지 하나만):"""

# 페르소나별 에이전트 안내 힌트 (user_profile_summary에 주입)
_PERSONA_HINTS: dict[str, str] = {
    "고령층": (
        "- 추정 페르소나: 고령층\n"
        "- 쉬운 단어와 짧은 문장을 쓰세요. 금융 용어는 괄호 안에 쉬운 설명을 추가하세요.\n"
        "- 필요시 큰글 모드(설정 → 큰글도우미)를 안내하세요."
    ),
    "사회초년생": (
        "- 추정 페르소나: 사회초년생\n"
        "- 기초 개념부터 친절하게 설명하세요.\n"
        "- 청년도약계좌·청년형 ISA 등 청년 전용 상품을 적극 안내하세요."
    ),
    "주부": (
        "- 추정 페르소나: 주부\n"
        "- 가계 전체 관점에서 안내하세요.\n"
        "- 배우자·자녀 관련 소득공제·보험·청약 질문에 익숙하게 대응하세요."
    ),
    "직장인": (
        "- 추정 페르소나: 직장인\n"
        "- 연말정산·퇴직금·IRP 세액공제 등 근로소득 중심 절세를 우선 안내하세요."
    ),
    "중장년": (
        "- 추정 페르소나: 중장년\n"
        "- 노후 준비·보험 리모델링 관점을 중심으로 안내하세요.\n"
        "- 은퇴까지 남은 기간을 고려한 현실적인 플랜을 제시하세요."
    ),
}

_VALID_PERSONAS = set(_PERSONA_HINTS.keys())

# ── 답변 스타일 감지 ──────────────────────────────────────────────────────────
_STYLE_KEYWORDS: dict[str, list[str]] = {
    "brief":    ["간단히", "짧게", "요약해", "핵심만", "한 줄로", "간략히", "간단하게"],
    "detailed": ["자세히", "상세히", "구체적으로", "더 설명", "풀어서", "자세하게"],
    "example":  ["예시", "예를 들어", "사례로", "예시를", "예를들면"],
}

_STYLE_LABELS: dict[str, str] = {
    "brief":    "간결하게 (핵심 위주)",
    "detailed": "자세하게 (상세 설명)",
    "example":  "예시 포함",
}


def _detect_style(user_message: str) -> str:
    """발화에서 답변 스타일 선호를 감지. 감지 안 되면 빈 문자열."""
    for style, keywords in _STYLE_KEYWORDS.items():
        if any(kw in user_message for kw in keywords):
            return style
    return ""


def _extract_user_text(callback_context: CallbackContext) -> str:
    """CallbackContext에서 현재 사용자 발화 텍스트를 추출."""
    content = callback_context.user_content
    if not content or not content.parts:
        return ""
    return " ".join(
        p.text for p in content.parts if hasattr(p, "text") and p.text
    ).strip()


def _detect_persona(user_message: str) -> str:
    """LLM 퓨샷으로 페르소나 감지. 실패 시 빈 문자열 반환."""
    if not _FEWSHOT_BLOCK or not user_message:
        return ""
    try:
        client = genai.Client()
        prompt = _PERSONA_ROUTING_PROMPT.format(
            fewshot_block=_FEWSHOT_BLOCK,
            user_message=user_message[:300],
        )
        resp = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(temperature=0.0),
        )
        result = resp.text.strip().replace('"', "").replace("'", "")
        return result if result in _VALID_PERSONAS else ""
    except Exception:
        return ""


# ── 세션 상태 키 ──────────────────────────────────────────────────────────────
_SESSION_MEMORY_LOADED = "user:_memory_loaded"
_SESSION_PERSONA_DETECTED = "user:_persona_detected"


# ── 콜백 ─────────────────────────────────────────────────────────────────────
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
    # ── 1. 사용자 메모리 로드 (세션 최초 1회) ────────────────────────────────
    if not callback_context.state.get(_SESSION_MEMORY_LOADED):
        user_id = callback_context.user_id
        mem = load_user_memory(user_id)
        for key, state_key in [
            ("investment_profile", "user:investment_profile"),
            ("literacy_level",     "user:literacy_level"),
            ("preferred_style",    "user:preferred_style"),
        ]:
            if mem.get(key) and not callback_context.state.get(state_key):
                callback_context.state[state_key] = mem[key]
        if mem.get("product_interests") and not callback_context.state.get("user:product_interests"):
            callback_context.state["user:product_interests"] = mem["product_interests"]
        callback_context.state[_SESSION_MEMORY_LOADED] = True

    # ── 2. 현재 발화 추출 ────────────────────────────────────────────────────
    user_msg = _extract_user_text(callback_context)

    # ── 3. 페르소나 감지 (세션 최초 1회) ────────────────────────────────────
    if not callback_context.state.get(_SESSION_PERSONA_DETECTED):
        if user_msg:
            persona = _detect_persona(user_msg)
            if persona:
                callback_context.state["user:persona"] = persona
        callback_context.state[_SESSION_PERSONA_DETECTED] = True

    # ── 4. 답변 스타일 감지 (매 턴 — 사용자가 언제든 바꿀 수 있음) ───────────
    if user_msg:
        detected_style = _detect_style(user_msg)
        if detected_style:
            callback_context.state["user:preferred_style"] = detected_style

    # ── 5. 에이전트 스킬 메모리 동적 로드 ───────────────────────────────────
    agent_name = callback_context.agent_name
    skills = load_agent_skills(agent_name)
    callback_context.state["agent_skills"] = skills if skills.strip() else "아직 축적된 스킬 없음."

    # ── 6. user_profile_summary 구성 ─────────────────────────────────────────
    interests = list(callback_context.state.get("user:product_interests") or [])
    profile   = callback_context.state.get("user:investment_profile") or ""
    literacy  = callback_context.state.get("user:literacy_level") or ""
    persona   = callback_context.state.get("user:persona") or ""
    style     = callback_context.state.get("user:preferred_style") or ""

    lines = []
    if persona and persona in _PERSONA_HINTS:
        lines.append(_PERSONA_HINTS[persona])
    if profile:
        lines.append(f"- 투자성향: {profile}")
    if literacy:
        lines.append(f"- 금융이해도: {literacy}")
    if interests:
        lines.append(f"- 관심 상품: {', '.join(interests)}")
    if style and style in _STYLE_LABELS:
        lines.append(f"- 답변 선호: {_STYLE_LABELS[style]}")

    callback_context.state["user_profile_summary"] = (
        "\n".join(lines) if lines else "파악된 정보 없음"
    )
    return None


def _after_agent_callback(callback_context: CallbackContext):
    if callback_context.state.get("user:memory_consent") == "declined":
        return None

    user_id   = callback_context.user_id
    profile   = callback_context.state.get("user:investment_profile") or ""
    literacy  = callback_context.state.get("user:literacy_level") or ""
    interests = list(callback_context.state.get("user:product_interests") or [])
    style     = callback_context.state.get("user:preferred_style") or ""

    if profile or literacy or style:
        save_user_memory(user_id, {
            "investment_profile": profile,
            "literacy_level":     literacy,
            "product_interests":  interests,
            "preferred_style":    style,
        })
    return None
