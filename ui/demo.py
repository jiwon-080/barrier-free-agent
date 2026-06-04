"""
NH 배리어프리 에이전트 — 로컬 데모
실행: uv run streamlit run ui/demo.py
"""
import io
import re
import sys
from pathlib import Path

import streamlit as st
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.navigation_tool import navigate_ui
from app.user_memory import MEMORY_DIR

# ── 디자인 상수 ───────────────────────────────────────────────────────────────
NH_GREEN = "#00A550"
NH_LIGHT_GREEN = "#E8F5EE"
NH_HIGHLIGHT = "#FF6B00"

NH_CSS = f"""
<style>
/* 본문 여백 최소화 및 모바일 너비 시뮬레이션 */
.block-container {{ padding: 1rem 0 80px 0 !important; max-width: 440px !important; }}
header {{ display: none !important; }}

/* 메뉴 항목 */
.nh-menu {{ background: white; border-bottom: 1px solid #F0F0F0;
           padding: 14px 16px; font-size: 16px; }}
.nh-menu:hover {{ background: {NH_LIGHT_GREEN}; }}

/* 섹션 구분 라벨 */
.nh-section {{ color: #888; font-size: 12px; padding: 10px 0 4px;
               font-weight: 600; letter-spacing: 0.4px; }}

/* 하이라이트 박스 */
.nh-highlight {{ border: 2.5px solid {NH_HIGHLIGHT}; border-radius: 8px;
                 background: #FFF3E0; padding: 10px 14px; margin: 4px 0;
                 animation: pulse 1.5s infinite; }}
@keyframes pulse {{
    0%   {{ box-shadow: 0 0 0 0   rgba(255,107,0,0.4); }}
    70%  {{ box-shadow: 0 0 0 8px rgba(255,107,0,0);   }}
    100% {{ box-shadow: 0 0 0 0   rgba(255,107,0,0);   }}
}}

/* 에이전트 말풍선 */
.agent-bubble {{ background: {NH_LIGHT_GREEN}; border-radius: 0 12px 12px 12px;
                 padding: 12px 16px; font-size: 15px; line-height: 1.7;
                 border-left: 3px solid {NH_GREEN}; margin-bottom: 8px; }}

/* Streamlit 버튼 전체 너비 기본화 */
div[data-testid="stHorizontalBlock"] .stButton button {{ width: 100%; }}

/* 금융상품 그리드 버튼 — 아이콘+라벨 줄바꿈, 카드 높이 */
div[data-testid="stHorizontalBlock"] .stButton button {{
    white-space: pre-wrap;
    line-height: 1.5;
}}
div[data-testid="stHorizontalBlock"] .stButton button p {{
    white-space: pre-wrap;
}}

/* 홈 배너 버튼 */
button[data-testid="baseButton-secondary"][key="home_agent_banner"],
div:has(> button[key="home_agent_banner"]) button {{
    border: 2px solid {NH_GREEN} !important;
    border-radius: 24px !important;
    color: {NH_GREEN} !important;
    background: white !important;
    font-size: 15px !important;
    font-weight: bold !important;
    padding: 12px 20px !important;
    box-shadow: none !important;
}}

/* 약관 AI 형광펜 */
mark.hl-red    {{ background: #FFCCCC; color: #8B0000; padding: 0 3px; border-radius: 2px; }}
mark.hl-orange {{ background: #FFE0B2; color: #7A3B00; padding: 0 3px; border-radius: 2px; }}
mark.hl-yellow {{ background: #FFF9C4; color: #4B3800; padding: 0 3px; border-radius: 2px; }}
</style>
"""

# ── FAB + 바텀시트 다이얼로그 CSS ─────────────────────────────────────────────
DIALOG_CSS = f"""
<style>
/* ── FAB 플로팅 버튼 ── */
.fab-wrapper {{
    position: fixed;
    bottom: 76px;
    right: 20px;
    z-index: 1000;
}}
.fab-wrapper button {{
    width: 58px !important;
    height: 58px !important;
    border-radius: 50% !important;
    background-color: {NH_GREEN} !important;
    color: white !important;
    font-size: 22px !important;
    padding: 0 !important;
    line-height: 1 !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(0,165,80,0.45) !important;
    min-height: unset !important;
    transition: transform 0.15s ease;
}}
.fab-wrapper button:hover {{
    transform: scale(1.08);
}}

/* ── 바텀시트 다이얼로그 ── */
div[data-testid="stDialog"] > div > div[role="dialog"] {{
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    top: auto !important;
    width: 440px !important;
    max-width: 100vw !important;
    border-radius: 20px 20px 0 0 !important;
    max-height: 65vh !important;
    overflow-y: auto !important;
    animation: slideUp 0.22s ease-out !important;
    padding-bottom: 16px !important;
}}
@keyframes slideUp {{
    from {{ transform: translateX(-50%) translateY(60%); opacity: 0.4; }}
    to   {{ transform: translateX(-50%) translateY(0);   opacity: 1; }}
}}

/* 드래그 핸들 */
div[data-testid="stDialog"] > div > div[role="dialog"]::before {{
    content: '';
    display: block;
    width: 36px;
    height: 4px;
    background: #DDD;
    border-radius: 2px;
    margin: 8px auto 12px;
}}

/* 예시 칩 / SUGGEST 액션 버튼 */
.chip-row button {{
    border-radius: 20px !important;
    border: none !important;
    color: white !important;
    background: {NH_GREEN} !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    min-height: unset !important;
    height: 36px !important;
    box-shadow: 0 2px 6px rgba(0,165,80,0.35) !important;
}}

/* 사용자 말풍선 */
.user-bubble {{
    background: {NH_GREEN};
    color: white;
    border-radius: 12px 12px 0 12px;
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.6;
    margin: 4px 0 4px 40px;
    text-align: right;
}}

/* 에이전트 말풍선 (다이얼로그 내부용) */
.bot-bubble {{
    background: #F4F4F4;
    border-radius: 12px 12px 12px 0;
    padding: 10px 14px;
    font-size: 14px;
    line-height: 1.6;
    margin: 4px 40px 4px 0;
}}

/* ── 하단 탭바 ── */
/* :has() — Chrome 105+, Safari 15.4+ 지원 */
[data-testid="stVerticalBlock"]:has(#tab-bar-marker)
  > [data-testid="stHorizontalBlock"]:last-child {{
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 440px !important;
    max-width: 100vw !important;
    background: white !important;
    border-top: 1px solid #EBEBEB !important;
    padding: 4px 0 12px !important;
    z-index: 998 !important;
    margin: 0 !important;
    gap: 0 !important;
}}
/* 탭 버튼 기본 */
[data-testid="stVerticalBlock"]:has(#tab-bar-marker)
  > [data-testid="stHorizontalBlock"]:last-child
  button {{
    background: transparent !important;
    border: none !important;
    border-top: 2px solid transparent !important;
    box-shadow: none !important;
    color: #999 !important;
    font-size: 11px !important;
    height: 48px !important;
    min-height: unset !important;
    border-radius: 0 !important;
    padding: 4px 4px 8px !important;
    transition: none !important;
}}
/* 활성 탭 (type="primary" → data-testid="baseButton-primary") */
[data-testid="stVerticalBlock"]:has(#tab-bar-marker)
  > [data-testid="stHorizontalBlock"]:last-child
  button[data-testid="baseButton-primary"] {{
    color: {NH_GREEN} !important;
    border-top: 2.5px solid {NH_GREEN} !important;
    font-weight: 700 !important;
    background: transparent !important;
}}
</style>
"""

# ── 탭바 정의 ────────────────────────────────────────────────────────────────
_TABS = [
    ("🏠", "홈",     "home"),
    ("💳", "금융상품", "financial_products"),
    ("📊", "내자산",  "my_assets"),
]
# 각 탭에 속하는 route 목록
_TAB_ROUTES = {
    "home": {"home"},
    "financial_products": {
        "financial_products", "financial_products/isa",
        "retirement_pension", "irp_new",
        "irp_tax_saving", "my_pension", "portfolio",
        "investment_diagnosis", "pension_design",
    },
    "my_assets": {"my_assets"},
}

def _active_tab(route: str) -> str:
    for tab_key, routes in _TAB_ROUTES.items():
        if route in routes:
            return tab_key
    # navigation_tool 반환 route가 "financial_products/xxx" 형태일 때
    if route.startswith("financial_products"):
        return "financial_products"
    return "home"


# ── ADK Agent 러너 ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_session_service() -> InMemorySessionService:
    svc = InMemorySessionService()
    svc.create_session_sync(
        app_name="app", user_id="demo_user", session_id="demo_session"
    )
    return svc

@st.cache_resource(show_spinner=False)
def _get_runner() -> Runner:
    from app.agent import root_agent
    return Runner(agent=root_agent, session_service=_get_session_service(), app_name="app")

def get_user_profile() -> dict:
    """ADK 세션 state에서 사용자 프로필 읽기 (단일 소스)."""
    try:
        svc = _get_session_service()
        session = svc.get_session_sync(
            app_name="app", user_id="demo_user", session_id="demo_session"
        )
        if session is None:
            return {}
        return {
            "investment_profile": session.state.get("user:investment_profile", ""),
            "literacy_level":     session.state.get("user:literacy_level", ""),
            "product_interests":  session.state.get("user:product_interests", []),
        }
    except Exception:
        return {}


def _set_profile_direct(investment_profile: str = "", literacy_level: str = "") -> None:
    """에이전트 호출 없이 ADK 세션 state에 직접 프로필 저장."""
    try:
        svc = _get_session_service()
        session = svc.get_session_sync(
            app_name="app", user_id="demo_user", session_id="demo_session"
        )
        if session is None:
            return
        if investment_profile:
            session.state["user:investment_profile"] = investment_profile
        if literacy_level:
            session.state["user:literacy_level"] = literacy_level
    except Exception:
        pass


def _reset_user_memory() -> None:
    """파일 메모리 + 세션 상태 모두 초기화."""
    from app.user_memory import delete_user_memory
    delete_user_memory("demo_user")
    try:
        svc = _get_session_service()
        session = svc.get_session_sync(
            app_name="app", user_id="demo_user", session_id="demo_session"
        )
        if session:
            for key in ["user:investment_profile", "user:literacy_level",
                        "user:product_interests", "user:_memory_loaded"]:
                session.state.pop(key, None)
    except Exception:
        pass
    st.session_state.pop("_ui_inv", None)
    st.session_state.pop("_ui_literacy", None)
    st.session_state.pop("_memory_consent", None)


def _fallback_highlight(text: str) -> str:
    """LLM이 mark 태그를 적용하지 않은 경우 Python regex로 하이라이트 적용."""
    import re, html as _html
    safe = _html.escape(text)
    red = [
        r"원금이 보장되지 않습니다",
        r"원금 손실이 발생할 수 있",
        r"예금자보호법 적용 대상이 아닙니다",
        r"그 책임은 가입자 본인에게 있습니다",
        r"원금의 일부 또는 전부를 잃을 수 있",
    ]
    orange = [
        r"기타소득세 16\.5%",
        r"해약수수료",
        r"중도해지 시",
        r"세액공제 혜택이 소급 취소",
        r"추징세액이 발생",
        r"중도인출은 불가",
        r"원금의 1\.5%",
    ]
    yellow = [
        r"연금소득세\(3\.3~5\.5%\)",
        r"연금소득세\(3\.3&#126;5\.5%\)",
        r"만 55세 이상",
        r"가입기간 5년 이상",
        r"연간 납입 한도",
        r"세액공제 한도",
    ]
    for p in red:
        safe = re.sub(p, lambda m: f'<mark class="hl-red">{m.group()}</mark>', safe)
    for p in orange:
        safe = re.sub(p, lambda m: f'<mark class="hl-orange">{m.group()}</mark>', safe)
    for p in yellow:
        safe = re.sub(p, lambda m: f'<mark class="hl-yellow">{m.group()}</mark>', safe)
    return safe


@st.cache_data(show_spinner=False)
def analyze_terms() -> str:
    """약관 원문을 읽고 Python 규칙 기반으로 위험 조항 위치에 하이라이트를 적용합니다.
    AI 해석 없이 패턴 매칭으로만 동작합니다 (금소법 준수)."""
    path = Path(__file__).parent.parent / "data" / "tos" / "irp_terms.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return f"(약관 파일을 불러오지 못했습니다: {e})"
    return _fallback_highlight(text)


@st.dialog("상품설명서 — 주의 조항 자동 표시")
def show_terms_dialog():
    st.markdown(
        '<div style="font-size:12px;line-height:1.7;margin-bottom:10px;">'
        '🤖 AI가 주요 위험 조항을 자동으로 표시했습니다.<br>'
        '<mark class="hl-red">빨강</mark> 원금손실·예금자보호 미적용 &nbsp;'
        '<mark class="hl-orange">주황</mark> 수수료·해지불이익 &nbsp;'
        '<mark class="hl-yellow">노랑</mark> 과세·의무기간·수령조건'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.spinner("위험 조항 위치 표시 중..."):
        html = analyze_terms()
    st.markdown(
        f'<div style="font-size:13px;line-height:1.9;white-space:pre-wrap;'
        f'word-break:keep-all;overflow-wrap:break-word;">{html}</div>',
        unsafe_allow_html=True,
    )


_TOOL_LABELS: dict[str, str] = {
    "navigate_ui":                "📍 화면 경로 탐색 중... 🐕",
    "get_irp_info":               "📋 IRP 상품 정보 조회 중... 🐕",
    "get_isa_info":               "📋 ISA 상품 정보 조회 중... 🐕",
    "explain_financial_term":     "📚 금융 용어 사전 검색 중... 🐱",
    "check_investment_guardrail": "🛡 투자 적합성 검토 중... 🐱",
    "search_products":            "🔍 예·적금 상품 검색 중... 🐱",
    "get_product_detail":         "🔍 상품 상세 정보 조회 중... 🐱",
    "compare_products":           "⚖️ 상품 비교 중... 🐱",
    "get_etf_price":              "📈 ETF 시세 조회 중... 🐱",
    "get_etf_prices_by_keyword":  "📈 ETF 시세 조회 중... 🐱",
    "get_macro_indicators":       "📊 거시경제 지표 조회 중... 🐱",
    "investment_agent":           "🐱 나비에게 연결 중...",
    "pension_tax_agent":          "🐦 까치에게 연결 중...",
    "simulation_agent":           "🐿️ 토리 계산 중...",
    "fraud_detection_agent":      "🐯 호야 위험도 판정 중...",
    "calculate_tax_saving":       "🧮 세액공제 환급액 계산 중... 🐿️",
    "calculate_maturity_amount":  "🧮 만기 수령액 계산 중... 🐿️",
    "calculate_pension_payout":   "🧮 연금 수령액 계산 중... 🐿️",
    "check_fraud_pattern":        "🔍 금융사기 패턴 분석 중... 🐯",
    "request_terms_analysis":     "📄 약관 위험 조항 분석 준비 중... 🐕",
    "set_user_profile":           "👤 투자성향 기록 중... 🐕",
}


def run_agent(query: str, on_step=None) -> dict:
    """ADK 에이전트 실행 → {"text", "route", "consent", "highlight", "warnings", "suggest_actions"}"""
    result = {
        "text": "", "route": None, "consent": "", "highlight": None,
        "warnings": [], "suggest_actions": [], "nav_steps": [],
        "show_terms": False,
    }
    try:
        runner = _get_runner()
        message = genai_types.Content(
            role="user", parts=[genai_types.Part.from_text(text=query)]
        )
        for event in runner.run(
            new_message=message,
            user_id="demo_user",
            session_id="demo_session",
            run_config=RunConfig(streaming_mode=StreamingMode.NONE),
        ):
            for fc in (event.get_function_calls() or []):
                if on_step and fc.name in _TOOL_LABELS:
                    on_step(_TOOL_LABELS[fc.name])
                if fc.name == "navigate_ui":
                    nav = navigate_ui(fc.args.get("screen_name", ""))
                    if nav.get("type") == "navigation":
                        result["route"]      = nav["route"]
                        result["consent"]    = nav["consent_message"]
                        result["highlight"]  = nav.get("highlight_target")
                        result["nav_steps"]  = nav.get("steps", [])

                # 구조화 도구 인터셉트 — LLM 텍스트 포맷에 의존하지 않고 직접 추출
                elif fc.name == "get_isa_info":
                    from app.product_tool import get_isa_info  # noqa: PLC0415
                    info = get_isa_info(fc.args.get("isa_type", "전체"))
                    if isinstance(info, dict):
                        result["warnings"]        = info.get("경고사항", [])
                        result["suggest_actions"] = info.get("추천다음단계", [])

                elif fc.name == "get_irp_info":
                    from app.product_tool import get_irp_info  # noqa: PLC0415
                    info = get_irp_info()
                    if isinstance(info, dict):
                        result["warnings"]        = info.get("경고사항", [])
                        result["suggest_actions"] = info.get("추천다음단계", [])

                elif fc.name == "request_terms_analysis":
                    result["show_terms"] = True

            if event.is_final_response() and event.content and event.content.parts:
                result["text"] = "".join(
                    p.text for p in event.content.parts if p.text
                )

    except Exception as e:
        result["text"] = f"오류가 발생했습니다. 잠시 후 다시 시도해 주세요.\n({e!s:.120})"

    if not result["text"]:
        result["text"] = "죄송합니다, 다시 말씀해 주세요."
    return result


# ── 생각 중 오버레이 카드 ─────────────────────────────────────────────────────
def _thinking_card(label: str) -> str:
    return (
        f'<div style="background:{NH_LIGHT_GREEN};border-radius:10px;'
        f'padding:14px 18px;text-align:center;margin:8px 0;">'
        f'<div style="font-size:18px;margin-bottom:4px;">⏳</div>'
        f'<div style="font-size:13px;font-weight:600;color:{NH_GREEN};">{label}</div>'
        f'</div>'
    )


# ── TTS ──────────────────────────────────────────────────────────────────────
def tts_audio_bytes(text: str) -> bytes | None:
    try:
        from gtts import gTTS  # noqa: PLC0415
        buf = io.BytesIO()
        gTTS(text=text[:400], lang="ko").write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None



# ── 라우트 정의 ───────────────────────────────────────────────────────────────
ROUTE_TITLES = {
    "home":                     "NH올원뱅크",
    "financial_products":       "금융상품",
    "financial_products/isa":   "ISA 개인종합자산관리계좌",
    "retirement_pension":       "퇴직연금",
    "irp_new":                  "IRP 신규가입/입금",
    "irp_tax_saving":           "개인형 IRP 세액공제용",
    "my_pension":               "MY퇴직연금",
    "portfolio":                "포트폴리오",
    "investment_diagnosis":     "투자 성향 진단",
    "pension_design":           "연금설계",
    "my_assets":                "내 자산",
}

# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "current_route":    "home",
        "history":          [],
        "highlight_target": None,
        "pending_route":    None,
        "pending_consent":  "",
        "pending_voice":    "",
        "agent_message":    "",
        # 멀티스텝 내비게이션
        "nav_steps":        [],
        "nav_step_idx":     0,
        "pending_nav_steps": [],
        # 에이전트 팝업
        "chat_history":     [],   # [{"role": "user"|"bot", "text": str}]
        "chip_selected":    "",
        "pending_query":    "",
        # TTS
        "tts_audio":        None,
        "reopen_popup":     False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── 내비게이션 헬퍼 ───────────────────────────────────────────────────────────
def go(route: str):
    st.session_state["history"].append(st.session_state["current_route"])
    st.session_state["current_route"] = route
    st.session_state["pending_route"] = None

    nav_steps = st.session_state.get("nav_steps", [])
    nav_idx = st.session_state.get("nav_step_idx", 0)
    if nav_steps:
        next_idx = nav_idx + 1
        if next_idx < len(nav_steps) and nav_steps[next_idx]["route"] == route:
            if next_idx == len(nav_steps) - 1:
                # 마지막 단계 도착 — 시퀀스 종료, 목적지 하이라이트만 유지
                st.session_state["nav_steps"] = []
                st.session_state["nav_step_idx"] = 0
                st.session_state["highlight_target"] = nav_steps[next_idx].get("highlight")
            else:
                st.session_state["nav_step_idx"] = next_idx
                st.session_state["highlight_target"] = nav_steps[next_idx].get("highlight")
        else:
            # 경로 이탈 — 시퀀스 종료
            st.session_state["nav_steps"] = []
            st.session_state["nav_step_idx"] = 0
            st.session_state["highlight_target"] = None
    else:
        st.session_state["highlight_target"] = None

def go_back():
    if st.session_state["history"]:
        st.session_state["current_route"] = st.session_state["history"].pop()
        st.session_state["highlight_target"] = None
        st.session_state["nav_steps"] = []
        st.session_state["nav_step_idx"] = 0

def is_hl(label: str) -> bool:
    return st.session_state.get("highlight_target") == label

def render_nav_badge():
    nav_steps = st.session_state.get("nav_steps", [])
    if not nav_steps:
        return
    idx = st.session_state.get("nav_step_idx", 0)
    if idx >= len(nav_steps):
        return
    step = nav_steps[idx]
    total = len(nav_steps)
    instruction = step.get("instruction", "")
    st.markdown(
        f'<div style="position:fixed;top:54px;left:50%;transform:translateX(-50%);'
        f'width:438px;max-width:calc(100vw - 4px);background:{NH_HIGHLIGHT};color:white;'
        f'padding:8px 16px;z-index:997;border-radius:0 0 8px 8px;'
        f'text-align:center;font-size:13px;font-weight:700;'
        f'box-shadow:0 3px 10px rgba(255,107,0,0.4);">'
        f'{idx + 1}/{total}단계 &nbsp;👇&nbsp; {instruction}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── 공통 헤더 ─────────────────────────────────────────────────────────────────
def render_header():
    route = st.session_state["current_route"]

    if route == "home":
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(
                f'<span style="background:{NH_GREEN};color:white;padding:4px 14px;'
                f'border-radius:20px;font-size:14px;font-weight:bold;">큰글 ●</span>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div style="text-align:right;font-size:14px;color:#666;padding-top:2px;">'
                "알림함&nbsp;&nbsp;메뉴</div>",
                unsafe_allow_html=True,
            )
    else:
        title = ROUTE_TITLES.get(route, "")
        c1, c2, _ = st.columns([1, 5, 1])
        with c1:
            if st.button("◀", key="hdr_back"):
                go_back()
                st.rerun()
        with c2:
            st.markdown(
                f'<div style="text-align:center;font-weight:bold;font-size:17px;'
                f'padding-top:2px;">{title}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

# ── 메뉴 아이템 컴포넌트 ──────────────────────────────────────────────────────
def menu_item(label: str, route: str, icon: str = ""):
    highlighted = is_hl(label)
    display = f"{'🔶 ' if highlighted else ''}{icon + ' ' if icon else ''}{label}  ›"

    if highlighted:
        st.markdown(
            f'<div class="nh-highlight">👇 <b>{label}</b> 을(를) 눌러주세요!</div>',
            unsafe_allow_html=True,
        )

    if st.button(display, key=f"nav_{route}", use_container_width=True):
        go(route)
        st.rerun()

    if not highlighted:
        st.markdown('<hr style="margin:0;border:none;border-top:1px solid #F0F0F0;">', unsafe_allow_html=True)

def section_label(text: str):
    st.markdown(
        f'<div class="nh-section">{text}</div>',
        unsafe_allow_html=True,
    )

# ── 에이전트 팝업 (바텀시트 다이얼로그) ──────────────────────────────────────
@st.dialog("배리어프리 도우미")
def agent_popup():
    # ── 표시용 프로필 동기화 (dialog 열릴 때마다 ADK state → st.session_state) ──
    _p = get_user_profile()
    if _p.get("investment_profile"):
        st.session_state["_ui_inv"]      = _p["investment_profile"]
    if _p.get("literacy_level"):
        st.session_state["_ui_literacy"] = _p["literacy_level"]

    # ── 펜딩 쿼리 처리 — 다이얼로그 내부에서 직접 실행 ──
    pending = st.session_state.get("pending_query", "")
    if pending:
        st.session_state["pending_query"] = ""
        st.session_state["chat_history"].append({"role": "user", "text": pending})
        thinking_ph = st.empty()
        thinking_ph.markdown(_thinking_card("🤔 도우미가 생각하고 있습니다..."), unsafe_allow_html=True)
        result = run_agent(
            pending,
            on_step=lambda lbl: thinking_ph.markdown(_thinking_card(lbl), unsafe_allow_html=True),
        )
        thinking_ph.empty()
        st.session_state["chat_history"].append({
            "role": "bot",
            "text": result["text"],
            "warnings": result.get("warnings", []),
            "suggest_actions": result.get("suggest_actions", []),
        })
        if result["route"]:
            st.session_state["pending_route"]     = result["route"]
            st.session_state["pending_consent"]   = result["consent"]
            st.session_state["highlight_target"]  = result["highlight"]
            st.session_state["pending_nav_steps"] = result.get("nav_steps", [])
        if result.get("show_terms"):
            st.session_state["pending_terms"] = True
        audio = tts_audio_bytes(_strip_markdown_for_tts(result["text"]))
        if audio:
            st.session_state["tts_audio"] = audio
        st.session_state["reopen_popup"] = True
        st.rerun()

    chat_history = st.session_state.get("chat_history", [])

    # ── 소개 영역 (대화 없을 때만 표시) ──
    if not chat_history:
        st.markdown(
            '<div style="text-align:center;padding:4px 0 12px;">'
            '<div style="font-size:40px;line-height:1.2;">💬</div>'
            '<div style="font-weight:700;font-size:15px;margin-top:6px;">안녕하세요, 배리어프리 도우미입니다!</div>'
            '<div style="color:#888;font-size:13px;margin-top:4px;line-height:1.5;">'
            '금융 용어 설명·화면 이동·상품 안내를<br>도와드립니다.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── 메모리 동의 배너 (최초 1회) ──
        if st.session_state.get("_memory_consent") is None:
            has_file = (MEMORY_DIR / "demo_user.md").exists()
            if not has_file:
                with st.container(border=True):
                    st.markdown(
                        '<div style="font-size:12px;line-height:1.6;color:#555;">'
                        '💾 <b>맞춤 안내 저장 안내</b><br>'
                        '다음 방문 시에도 투자성향·금융이해도를 기억해 드립니다.<br>'
                        '개인 식별 정보(이름·계좌)는 저장하지 않습니다.'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    mc1, mc2 = st.columns(2)
                    with mc1:
                        if st.button("✅ 동의", key="mem_agree", use_container_width=True, type="primary"):
                            st.session_state["_memory_consent"] = "granted"
                            st.rerun()
                    with mc2:
                        if st.button("❌ 거절", key="mem_decline", use_container_width=True):
                            st.session_state["_memory_consent"] = "declined"
                            # ADK 세션 state에도 거절 기록 → _after_agent_callback에서 저장 차단
                            try:
                                svc = _get_session_service()
                                sess = svc.get_session_sync(
                                    app_name="app", user_id="demo_user", session_id="demo_session"
                                )
                                if sess:
                                    sess.state["user:memory_consent"] = "declined"
                            except Exception:
                                pass
                            st.rerun()
            else:
                st.session_state["_memory_consent"] = "granted"

        # 사용자 프로필 배지 (표시용 캐시 우선, 없으면 ADK state)
        inv      = st.session_state.get("_ui_inv", "")
        literacy = st.session_state.get("_ui_literacy", "")
        interests = get_user_profile().get("product_interests", [])

        # 파일 메모리에서 로드된 경우 세션 UI 캐시 동기화
        if not inv or not literacy:
            _p = get_user_profile()
            if _p.get("investment_profile") and not inv:
                inv = _p["investment_profile"]
                st.session_state["_ui_inv"] = inv
            if _p.get("literacy_level") and not literacy:
                literacy = _p["literacy_level"]
                st.session_state["_ui_literacy"] = literacy

        if inv or literacy or interests:
            _LITERACY_LABEL = {"기초": "📗 기초", "일반": "📘 일반", "전문가": "📕 전문가"}
            chip_parts = (
                ([_LITERACY_LABEL.get(literacy, literacy)] if literacy else [])
                + ([inv] if inv else [])
                + interests[:2]
            )
            mem_icon = "💾" if (MEMORY_DIR / "demo_user.md").exists() else "👤"
            st.markdown(
                f'<div style="background:{NH_LIGHT_GREEN};border-radius:20px;'
                f'padding:5px 14px;font-size:12px;color:{NH_GREEN};'
                f'font-weight:600;display:inline-block;">'
                f'{mem_icon} {" · ".join(chip_parts)}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("🗑️ 기억 초기화", key="mem_reset", use_container_width=False):
                _reset_user_memory()
                st.rerun()

        # 금융이해도 미설정 시 선택 칩 표시
        if not literacy:
            st.markdown(
                '<div style="color:#555;font-size:12px;font-weight:600;margin-bottom:6px;">'
                '금융 이해도를 선택해 주세요</div>',
                unsafe_allow_html=True,
            )
            lc1, lc2, lc3 = st.columns(3)
            for label, col, key in [
                ("📗 기초",   lc1, "lit_basic"),
                ("📘 일반",   lc2, "lit_mid"),
                ("📕 전문가", lc3, "lit_expert"),
            ]:
                with col:
                    if st.button(label, key=key, use_container_width=True):
                        level = label.split(" ", 1)[1]
                        _set_profile_direct(literacy_level=level)
                        st.session_state["_ui_literacy"] = level  # 즉시 표시 반영
                        st.rerun()
            st.markdown('<div style="margin-bottom:10px;"></div>', unsafe_allow_html=True)

        st.markdown(
            '<div style="color:#555;font-size:12px;font-weight:600;margin-bottom:6px;">'
            '이런 걸 물어보세요</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        chips = [
            ("IRP가 뭔가요?",      c1, "chip_irp"),
            ("기준금리 알려줘",    c2, "chip_rate"),
            ("퇴직연금 가입",      c3, "chip_pension"),
            ("내 투자성향 진단해줘", c4, "chip_invest"),
        ]
        st.markdown('<div class="chip-row">', unsafe_allow_html=True)
        for label, col, key in chips:
            with col:
                if st.button(label, key=key, use_container_width=True):
                    st.session_state["pending_query"] = label
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

    # ── 대화 내역 ──
    else:
        # TTS 재생 (새 응답이 있을 때 한 번만)
        audio = st.session_state.get("tts_audio")
        if audio:
            st.audio(audio, format="audio/mp3", autoplay=True)
            del st.session_state["tts_audio"]

        # ── 화면 이동 동의 카드 — 다이얼로그 최상단에 표시 ──
        if st.session_state.get("pending_route"):
            with st.container(border=True):
                st.markdown(
                    f'📍 **{st.session_state["pending_consent"]}**',
                    unsafe_allow_html=False,
                )
                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button("✅ 네, 이동할게요", key="popup_yes",
                                 use_container_width=True, type="primary"):
                        nav_steps = st.session_state.get("pending_nav_steps", [])
                        if len(nav_steps) > 1:
                            st.session_state["nav_steps"] = nav_steps
                            st.session_state["nav_step_idx"] = 0
                            first = nav_steps[0]
                            st.session_state["history"].append(st.session_state["current_route"])
                            st.session_state["current_route"] = first["route"]
                            st.session_state["highlight_target"] = first.get("highlight")
                            st.session_state["pending_nav_steps"] = []
                            st.session_state["reopen_popup"] = False
                        else:
                            hl = st.session_state.get("highlight_target")
                            go(st.session_state["pending_route"])
                            st.session_state["highlight_target"] = hl
                            st.session_state["reopen_popup"] = True
                        st.session_state["pending_route"] = None
                        st.rerun()
                with no_col:
                    if st.button("❌ 아니오", key="popup_no",
                                 use_container_width=True):
                        st.session_state["pending_route"] = None
                        st.rerun()
            st.divider()

        for i, msg in enumerate(chat_history):
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-bubble">{msg["text"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                render_bot_message(msg, i)

        st.divider()

    # ── 입력창 (항상 표시) ──
    col_form, col_mic = st.columns([5, 1])

    with col_mic:
        from streamlit_mic_recorder import speech_to_text as _stt  # noqa: PLC0415
        stt_text = _stt(
            language="ko-KR",
            start_prompt="🎤",
            stop_prompt="⏹",
            just_once=True,
            key="stt_dialog",
        )
        if stt_text:
            st.session_state["pending_query"] = stt_text
            st.rerun()

    with col_form:
        with st.form(key="dialog_input_form", clear_on_submit=True, border=False):
            user_input = st.text_input(
                "질문",
                placeholder="무엇이든 물어보세요",
                label_visibility="collapsed",
            )
            if st.form_submit_button("전송 →", use_container_width=True, type="primary"):
                if user_input.strip():
                    st.session_state["pending_query"] = user_input.strip()
                    st.rerun()


# ── SUGGEST 칩 파서/렌더러 ────────────────────────────────────────────────────
_SUGGEST_RE = re.compile(r"\[SUGGEST:\s*([^|\]]+)\|([^\]]+)\]")


def _strip_suggest(text: str) -> str:
    return _SUGGEST_RE.sub("", text).strip()


def _strip_markdown_for_tts(text: str) -> str:
    text = _strip_suggest(text)
    text = re.sub(r"#{1,6}\s*", "", text)       # ### 헤더
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)  # **bold** / *italic*
    text = re.sub(r"`([^`]+)`", r"\1", text)    # `code`
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)  # > 인용
    text = re.sub(r"^[-*]\s+", "", text, flags=re.MULTILINE)  # - 목록
    return text.strip()


def render_bot_message(msg: dict, msg_idx: int):
    """Bot 메시지 렌더링.

    - warnings → > ⚠️ 강조 블록 (tool 구조화 데이터 직접 사용)
    - suggest_actions → 클릭 가능한 칩 버튼
    - LLM 텍스트의 [SUGGEST:...] 마커는 보조 fallback으로만 사용
    """
    text = msg if isinstance(msg, str) else msg.get("text", "")
    warnings = [] if isinstance(msg, str) else msg.get("warnings", [])
    suggest_actions = [] if isinstance(msg, str) else msg.get("suggest_actions", [])

    clean = _strip_suggest(text)
    # 단일 \n → \n\n 으로 정규화 (마크다운은 빈 줄이 있어야 단락 구분됨)
    clean = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', clean)

    with st.chat_message("assistant", avatar="🐕"):
        if "<mark" in clean:
            st.markdown(clean, unsafe_allow_html=True)
        else:
            st.markdown(clean)

    # 경고사항 — 각 항목을 개별 st.markdown() 호출로 분리 (줄바꿈 보장)
    if warnings:
        for w in warnings:
            st.markdown(
                f'<div style="background:#FFF3E0;border-left:4px solid #FF8C00;'
                f'padding:8px 12px;margin:3px 0;border-radius:0 6px 6px 0;'
                f'font-size:13px;line-height:1.6;word-break:keep-all;'
                f'overflow-wrap:break-word;">⚠️ {w}</div>',
                unsafe_allow_html=True,
            )

    # 추천 다음단계 칩 — 도구 구조화 데이터만 사용 (LLM 텍스트 파싱 제거)
    chips = [(a["route"], a["label"]) for a in suggest_actions]

    # irp_new / ISA 가입 칩은 consent + nav_steps flow로 처리
    _CHIP_CONSENT_MAP = {
        "irp_new": "IRP 신규가입",
        "financial_products/isa": "ISA 신규가입",
    }

    if chips:
        st.markdown('<div class="chip-row">', unsafe_allow_html=True)
        cols = st.columns(min(len(chips), 3))
        for col, (route, label) in zip(cols, chips):
            with col:
                if st.button(label, key=f"sug_{msg_idx}_{route}", use_container_width=True):
                    if route in _CHIP_CONSENT_MAP:
                        _nav = navigate_ui(_CHIP_CONSENT_MAP[route])
                        if _nav.get("type") == "navigation":
                            st.session_state["pending_route"]     = _nav["route"]
                            st.session_state["pending_consent"]   = _nav["consent_message"]
                            st.session_state["highlight_target"]  = _nav.get("highlight_target")
                            st.session_state["pending_nav_steps"] = _nav.get("steps", [])
                    else:
                        hl = st.session_state.get("highlight_target")
                        go(route)
                        st.session_state["highlight_target"] = hl
                    st.session_state["reopen_popup"] = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ── FAB 플로팅 버튼 ───────────────────────────────────────────────────────────
def render_fab():
    st.markdown('<div class="fab-wrapper">', unsafe_allow_html=True)
    if st.button("🤗", key="fab_agent", help="배리어프리 도우미"):
        agent_popup()
    st.markdown('</div>', unsafe_allow_html=True)


# ── 하단 탭바 ─────────────────────────────────────────────────────────────────
def render_tab_bar():
    active = _active_tab(st.session_state["current_route"])

    # CSS :has() 선택자의 앵커 마커 (빈 span)
    st.markdown('<span id="tab-bar-marker" style="display:none"></span>',
                unsafe_allow_html=True)

    cols = st.columns(3)
    for col, (icon, label, target) in zip(cols, _TABS):
        is_active = (active == target)
        with col:
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{icon} {label}",
                key=f"tab_{target}",
                type=btn_type,
                use_container_width=True,
            ):
                if target == "home":
                    st.session_state["history"] = []
                    st.session_state["current_route"] = "home"
                    st.session_state["highlight_target"] = None
                else:
                    go(target)
                st.rerun()


# ── 화면: 홈 ─────────────────────────────────────────────────────────────────
def screen_home():
    st.markdown("**홍길동** 님 &nbsp;›", unsafe_allow_html=True)
    st.caption("OO은행 · 다른금융")

    with st.container(border=True):
        st.markdown("##### OO은행 &nbsp; 356-&#42;&#42;&#42;&#42;-&#42;&#42;&#42;&#42;", unsafe_allow_html=True)
        st.button("잔액보기", use_container_width=True, key="home_balance")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("ATM출금", key="home_atm")
        with c2:
            st.button("거래내역", key="home_history")
        with c3:
            if st.button("이체", key="home_transfer", type="primary"):
                pass

    # 배리어프리 도우미 배너
    if st.button(
        "🤗 배리어프리 도우미에게 물어보세요",
        key="home_agent_banner",
        use_container_width=True,
    ):
        agent_popup()

    # 사용자 맞춤 프로필 카드 (데이터가 있을 때만)
    profile = get_user_profile()
    inv = profile.get("investment_profile", "")
    interests = profile.get("product_interests", [])
    if inv or interests:
        parts = []
        if inv:
            parts.append(f"**{inv}**")
        if interests:
            parts.append(" · ".join(interests[:4]))
        st.markdown(
            f'<div style="background:{NH_LIGHT_GREEN};border-left:3px solid {NH_GREEN};'
            f'padding:8px 12px;border-radius:0 6px 6px 0;font-size:13px;margin:4px 0;">'
            f'👤 맞춤 정보: {" &nbsp;|&nbsp; ".join(parts)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("#### 빠른 메뉴")
    _QUICK = [
        ("🏦", "전체계좌조회", None),
        ("💸", "ATM 출금",    None),
        ("📊", "금융상품",    "financial_products"),
        ("🛡️", "안전한금융",  None),
    ]
    c1, c2 = st.columns(2)
    for i, (icon, label, route) in enumerate(_QUICK):
        with (c1 if i % 2 == 0 else c2):
            if st.button(f"{icon}  {label}", key=f"home_q{i}", use_container_width=True):
                if route:
                    go(route)
                    st.rerun()

# ── 화면: 금융상품 ────────────────────────────────────────────────────────────
def screen_financial_products():
    # 해시태그 칩 필터 (시각적 완성도용)
    st.markdown(
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;">'
        + "".join(
            f'<span style="background:#F0F0F0;border-radius:20px;padding:4px 10px;'
            f'font-size:12px;color:#555;">#{tag}</span>'
            for tag in ["사회초년생", "직장인", "개인사업자", "은퇴준비"]
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    # 아이콘 그리드 (4열)
    _PRODUCTS = [
        ("🏦", "입출금",       None),
        ("💰", "예금",         None),
        ("🐷", "적금",         None),
        ("🏠", "주택청약",     None),
        ("📊", "펀드",         None),
        ("💳", "대출",         None),
        ("💱", "외환",         None),
        ("👴", "퇴직연금",     "retirement_pension"),
        ("🛡️", "보험",         None),
        ("🏛️", "신탁",         None),
        ("📋", "ISA",          "financial_products/isa"),
        ("📈", "IRP",          "irp_new"),
    ]

    cols = st.columns(4)
    for i, (icon, label, route) in enumerate(_PRODUCTS):
        with cols[i % 4]:
            if is_hl(label):
                st.markdown(
                    '<div class="nh-highlight" style="text-align:center;'
                    'font-size:11px;margin-bottom:2px;padding:4px 2px;">👇 눌러주세요</div>',
                    unsafe_allow_html=True,
                )
            clicked = st.button(
                f"{icon}\n{label}",
                key=f"fp_{label}",
                use_container_width=True,
                type="primary" if is_hl(label) else "secondary",
            )
            if clicked and route:
                go(route)
                st.rerun()

# ── 화면: 퇴직연금 ────────────────────────────────────────────────────────────
def screen_retirement_pension():
    menu_item("MY퇴직연금",        "my_pension",          "👤")
    menu_item("IRP 신규가입/입금", "irp_new",             "📋")
    menu_item("운용상품관리",      "asset_management",    "⚙️")
    menu_item("ETF 당일 매매/관리","etf_trade",           "📈")
    menu_item("연금계좌관리",      "pension_account",     "🗂️")
    menu_item("상품안내/설계",     "product_guide",       "📐")
    menu_item("알림 및 고객지원",  "support",             "🔔")

# ── 화면: IRP 신규가입/입금 ───────────────────────────────────────────────────
def screen_irp_new():
    section_label("퇴직연금 가입")
    menu_item("개인형 IRP 세액공제용",        "irp_tax_saving",  "✅")
    menu_item("개인형 IRP 퇴직금 수령용",     "irp_retirement",  "🏖️")
    menu_item("확정기여형 퇴직연금 (DC)",      "irp_dc",          "🏢")

    section_label("운용상품 조회")
    menu_item("예금",           "deposit_product",  "💰")
    menu_item("펀드",           "fund_product",     "📊")
    menu_item("ETF",            "etf_product",      "📈")
    menu_item("디폴트 옵션",    "default_option",   "⚙️")

    section_label("퇴직연금 관리")
    menu_item("MY퇴직연금",  "my_pension",      "👤")
    menu_item("포트폴리오",  "portfolio",       "🥧")
    menu_item("연금설계",    "pension_design",  "📐")

# ── 화면: 개인형 IRP 세액공제용 (최종 목적지) ────────────────────────────────
def screen_irp_tax_saving():
    with st.container(border=True):
        st.markdown("#### 개인형 IRP — 세액공제용")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("연간 납입 한도", "900만원")
        with c2:
            st.metric("세액공제율", "13.2 ~ 16.5%")
        st.caption("만 55세 이후 연금 형태로 수령 가능")

    if is_hl("가입확인"):
        st.markdown(
            '<div class="nh-highlight">👇 아래 항목을 꼼꼼히 읽고 확인해 주세요!</div>',
            unsafe_allow_html=True,
        )
    st.markdown("#### 가입 전 필수 확인")
    chk1 = st.checkbox("투자 위험 등급 확인 (필수)", key="irp_chk1")

    chk2_col, btn_col = st.columns([4, 1])
    with chk2_col:
        chk2 = st.checkbox("상품 설명서 확인 (필수)", key="irp_chk2")
    with btn_col:
        if st.button("보기", key="irp_terms_btn", use_container_width=True):
            show_terms_dialog()

    chk3 = st.checkbox("적합성 진단 완료 (필수)", key="irp_chk3")

    st.button(
        "다음 단계로 →",
        type="primary",
        use_container_width=True,
        key="irp_tax_next",
        disabled=not (chk1 and chk2 and chk3),
    )

# ── 화면: MY퇴직연금 ──────────────────────────────────────────────────────────
def screen_my_pension():
    with st.container(border=True):
        st.markdown("##### 총 적립금")
        st.markdown('<span style="font-size:28px;font-weight:bold;">12,350,000원</span>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("수익률", "+4.2%")
        with c2:
            st.metric("수익금", "+520,000원")

    with st.container(border=True):
        st.markdown("**목표 달성률**")
        st.progress(0.62, text="목표 2억원까지 62%")
        st.caption("예상 달성 시기: 2041년 (만 60세)")

    if st.button("포트폴리오 보기 →", key="my_pension_portfolio", use_container_width=True):
        go("portfolio")
        st.rerun()

# ── 화면: 포트폴리오 ──────────────────────────────────────────────────────────
def screen_portfolio():
    import pandas as pd

    st.markdown("##### 운용 자산 구성")
    df = pd.DataFrame({
        "상품": ["예금", "채권형 펀드", "혼합형 ETF"],
        "비중": ["50%", "30%", "20%"],
        "수익률": ["+3.5%", "+2.8%", "+8.1%"],
        "평가금액": ["6,175,000원", "3,705,000원", "2,470,000원"],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### 위험 지표")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("변동성", "4.2%")
    with c2:
        st.metric("샤프 비율", "0.85")
    with c3:
        st.metric("최대 낙폭", "-3.1%")

# ── 화면: 투자 성향 진단 ──────────────────────────────────────────────────────
_Q1_SCORE = {
    "원금 보전이 최우선": 1, "안정적 수익 추구": 2,
    "시장 평균 이상 수익": 3, "고위험 고수익 추구": 4,
}
_Q2_SCORE = {"1년 미만": 1, "1~3년": 2, "3~5년": 3, "5년 이상": 4}
_Q3_SCORE = {"원금 손실 불가": 1, "5% 미만": 2, "10~20% 가능": 3, "20% 이상도 감수": 4}

def _score_to_profile(q1: str, q2: str, q3: str) -> str:
    total = _Q1_SCORE[q1] + _Q2_SCORE[q2] + _Q3_SCORE[q3]
    if total <= 6:
        return "위험회피형"
    elif total <= 9:
        return "위험중립형"
    return "위험선호형"

def screen_investment_diagnosis():
    st.warning("⚠️ ETF·펀드 등 고위험 상품 이용 전 투자 성향 진단이 필요합니다.")

    # 이미 진단 완료된 경우 현재 성향 표시
    current = get_user_profile().get("investment_profile", "")
    if current:
        _PROFILE_ICON = {"위험회피형": "🟢", "위험중립형": "🟡", "위험선호형": "🔴"}
        st.success(
            f"{_PROFILE_ICON.get(current, '✅')} 현재 투자성향: **{current}**\n\n"
            "다시 진단하려면 아래 문항을 작성하고 제출하세요."
        )

    with st.form("diagnosis_form"):
        st.markdown("#### Q1. 투자 목적은 무엇인가요?")
        q1 = st.radio(
            "Q1",
            ["원금 보전이 최우선", "안정적 수익 추구", "시장 평균 이상 수익", "고위험 고수익 추구"],
            label_visibility="collapsed",
            key="diag_q1",
        )

        st.markdown("#### Q2. 투자 가능 기간은?")
        q2 = st.radio(
            "Q2",
            ["1년 미만", "1~3년", "3~5년", "5년 이상"],
            label_visibility="collapsed",
            key="diag_q2",
        )

        st.markdown("#### Q3. 투자 손실 발생 시 감내 가능한 수준은?")
        q3 = st.radio(
            "Q3",
            ["원금 손실 불가", "5% 미만", "10~20% 가능", "20% 이상도 감수"],
            label_visibility="collapsed",
            key="diag_q3",
        )

        if st.form_submit_button("진단 완료", use_container_width=True, type="primary"):
            profile = _score_to_profile(q1, q2, q3)
            _set_profile_direct(investment_profile=profile)
            st.session_state["_ui_inv"] = profile  # 즉시 표시 반영
            st.success(f"✅ 투자성향이 **{profile}**으로 저장되었습니다.")

# ── 화면: 연금설계 ────────────────────────────────────────────────────────────
def screen_pension_design():
    st.markdown("#### 은퇴 시뮬레이션")
    with st.form("pension_form"):
        age = st.slider("현재 나이", 20, 65, 40)
        monthly = st.number_input("월 납입액 (만원)", min_value=1, max_value=150, value=30)
        retire_age = st.slider("은퇴 목표 나이", age + 1, 70, 60)

        if st.form_submit_button("계산하기", use_container_width=True, type="primary"):
            years = retire_age - age
            total = monthly * 12 * years
            with_interest = int(total * 1.035 ** years / monthly / 12) * monthly * 12
            st.success(
                f"📊 {years}년간 월 {monthly}만원 납입 시 "
                f"예상 적립금: **약 {with_interest:,}만원**\n\n"
                f"*(연 3.5% 복리 가정)*"
            )

# ── 화면: ISA ────────────────────────────────────────────────────────────────
def screen_isa():
    if is_hl("ISA가입"):
        st.markdown(
            '<div class="nh-highlight">👇 <b>신탁형</b> 또는 <b>일임형</b> 중 하나를 선택해 주세요. 차이가 궁금하시면 물어보세요!</div>',
            unsafe_allow_html=True,
        )
    tab_trust, tab_managed = st.tabs(["신탁형", "일임형"])

    with tab_trust:
        st.markdown("#### ISA 신탁형")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("비과세 한도", "200만원 / 년")
        with c2:
            st.metric("가입 한도", "연 2,000만원")
        with st.container(border=True):
            st.markdown(
                "- 투자자가 **직접 종목·수량 지정** 운용\n"
                "- 예·적금, 펀드, ETF, ELS 등 자유 편입\n"
                "- 손익 통산 후 순이익 200만원까지 비과세\n"
                "- 의무 가입 기간: **3년**"
            )

    with tab_managed:
        st.markdown("#### ISA 일임형")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("비과세 한도", "200만원 / 년")
        with c2:
            st.metric("운용 유형", "초저위험~고위험")
        with st.container(border=True):
            st.markdown(
                "- **전문가가 투자 성향에 맞게 포트폴리오 운용**\n"
                "- 5단계 위험등급 모델 포트폴리오 제공\n"
                "- 서민·농어민형: 비과세 400만원\n"
                "- 의무 가입 기간: **3년**"
            )
        st.select_slider(
            "투자 성향 선택",
            options=["초저위험", "저위험", "중위험", "고위험", "초고위험"],
            value="중위험",
            key="isa_risk",
        )

    # ── 가입 전 필수 확인 (탭 외부) ──────────────────────────────────────────
    if is_hl("ISA가입"):
        st.markdown(
            '<div class="nh-highlight">👇 아래 항목을 꼼꼼히 읽고 확인해 주세요!</div>',
            unsafe_allow_html=True,
        )
    st.markdown("#### 가입 전 필수 확인")
    isa_chk1 = st.checkbox("투자 위험 등급 확인 (필수)", key="isa_chk1")

    isa_chk2_col, isa_btn_col = st.columns([4, 1])
    with isa_chk2_col:
        isa_chk2 = st.checkbox("상품 설명서 확인 (필수)", key="isa_chk2")
    with isa_btn_col:
        if st.button("보기", key="isa_terms_btn", use_container_width=True):
            show_terms_dialog()

    isa_chk3 = st.checkbox("적합성 진단 완료 (필수)", key="isa_chk3")

    st.button(
        "ISA 가입 신청 →",
        type="primary",
        use_container_width=True,
        key="isa_join_btn",
        disabled=not (isa_chk1 and isa_chk2 and isa_chk3),
    )


# ── 화면: 내 자산 ────────────────────────────────────────────────────────────
def screen_my_assets():
    st.markdown("#### 내 자산 현황")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.metric("총 자산", "47,350,000원", "+2.1%")
        with c2:
            st.metric("이번 달 수익", "+320,000원", "")

    st.markdown("##### 자산 구성")
    items = [
        ("🏦 예금·적금",   "12,350,000원", "26%"),
        ("📈 IRP·연금",    "12,350,000원", "26%"),
        ("💳 펀드·ETF",    "8,200,000원",  "17%"),
        ("🏠 기타",        "14,450,000원", "31%"),
    ]
    for icon_label, amount, pct in items:
        c1, c2, c3 = st.columns([4, 3, 1])
        with c1:
            st.markdown(icon_label)
        with c2:
            st.markdown(f'<div style="text-align:right">{amount}</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="text-align:right;color:#888;font-size:12px">{pct}</div>', unsafe_allow_html=True)
        st.markdown('<hr style="margin:4px 0;border-color:#F0F0F0">', unsafe_allow_html=True)


def _resolve_screen(route: str):
    """SCREEN_MAP에 없는 route를 prefix 매칭으로 fallback."""
    if route in SCREEN_MAP:
        return SCREEN_MAP[route]
    if route.startswith("financial_products"):
        return screen_financial_products
    return screen_home


SCREEN_MAP = {
    "home":                     screen_home,
    "financial_products":       screen_financial_products,
    "financial_products/isa":   screen_isa,
    # navigate_ui 실제 반환 route 별칭
    "financial_products/retirement_pension":          screen_retirement_pension,
    "retirement_pension":       screen_retirement_pension,
    "irp_new":                  screen_irp_new,
    "irp_tax_saving":           screen_irp_tax_saving,
    "my_pension":               screen_my_pension,
    "portfolio":                screen_portfolio,
    "investment_diagnosis":     screen_investment_diagnosis,
    "pension_design":           screen_pension_design,
    "my_assets":                screen_my_assets,
    "my_products":              screen_my_assets,
    "my_products/account":      screen_my_assets,
}

# ── 동의 UI ───────────────────────────────────────────────────────────────────
def render_consent_ui():
    if not st.session_state.get("pending_route"):
        return

    st.markdown("---")
    with st.container(border=True):
        st.markdown(
            f'<div class="agent-bubble">💬 &nbsp;{st.session_state["pending_consent"]}</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 네, 이동할게요", type="primary", use_container_width=True, key="consent_yes"):
                go(st.session_state["pending_route"])
                st.rerun()
        with c2:
            if st.button("❌ 아니오", use_container_width=True, key="consent_no"):
                st.session_state["pending_route"] = None
                st.session_state["highlight_target"] = None
                st.rerun()


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="NH 배리어프리 에이전트 데모",
        page_icon="🏦",
        layout="centered",
    )

    init_session()
    st.markdown(NH_CSS + DIALOG_CSS, unsafe_allow_html=True)

    # ── 약관 분석 다이얼로그 오픈 ──
    if st.session_state.get("pending_terms"):
        st.session_state["pending_terms"] = False
        show_terms_dialog()

    # ── 화면 이동 후 팝업 재오픈 (에이전트 대화 유지) ──
    elif st.session_state.get("reopen_popup"):
        st.session_state["reopen_popup"] = False
        agent_popup()

    # ── pending_query → 다이얼로그 내부에서 처리 ──
    elif st.session_state.get("pending_query"):
        agent_popup()

    render_header()
    render_nav_badge()

    route = st.session_state["current_route"]
    _resolve_screen(route)()

    render_tab_bar()   # 항상 마지막 — CSS :has(#tab-bar-marker) 의 last-child 매칭
    render_fab()


if __name__ == "__main__":
    main()
