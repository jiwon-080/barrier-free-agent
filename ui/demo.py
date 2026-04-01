"""
NH 배리어프리 에이전트 — 로컬 데모
실행: uv run streamlit run ui/demo.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.navigation_tool import navigate_ui

# ── 디자인 상수 ───────────────────────────────────────────────────────────────
NH_GREEN = "#00A550"
NH_LIGHT_GREEN = "#E8F5EE"
NH_HIGHLIGHT = "#FF6B00"

NH_CSS = f"""
<style>
/* 본문 여백 최소화 및 모바일 너비 시뮬레이션 */
.block-container {{ padding: 1rem 0 4rem 0 !important; max-width: 440px !important; }}
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
</style>
"""

# ── 라우트 정의 ───────────────────────────────────────────────────────────────
ROUTE_TITLES = {
    "home":                 "NH올원뱅크",
    "financial_products":   "금융상품",
    "retirement_pension":   "퇴직연금",
    "irp_new":              "IRP 신규가입/입금",
    "irp_tax_saving":       "개인형 IRP 세액공제용",
    "my_pension":           "MY퇴직연금",
    "portfolio":            "포트폴리오",
    "investment_diagnosis": "투자 성향 진단",
    "pension_design":       "연금설계",
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── 내비게이션 헬퍼 ───────────────────────────────────────────────────────────
def go(route: str):
    st.session_state["history"].append(st.session_state["current_route"])
    st.session_state["current_route"] = route
    st.session_state["highlight_target"] = None
    st.session_state["pending_route"] = None

def go_back():
    if st.session_state["history"]:
        st.session_state["current_route"] = st.session_state["history"].pop()
        st.session_state["highlight_target"] = None

def is_hl(label: str) -> bool:
    return st.session_state.get("highlight_target") == label

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
            f'<div class="nh-highlight">👆 <b>{label}</b> 을(를) 눌러주세요!</div>',
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

# ── 화면: 홈 ─────────────────────────────────────────────────────────────────
def screen_home():
    st.markdown("**홍길동** 님 &nbsp;›", unsafe_allow_html=True)
    st.caption("NH농협 · 다른금융")

    with st.container(border=True):
        st.markdown("##### NH농협은행 &nbsp; 356-\*\*\*\*-\*\*\*\*")
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
    st.markdown(
        f'<div style="border:2px solid {NH_GREEN};border-radius:24px;padding:12px 20px;'
        f'text-align:center;font-size:15px;color:{NH_GREEN};font-weight:bold;margin:8px 0;">'
        "🤖 배리어프리 도우미에게 물어보세요</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### 빠른 메뉴")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("🏦&nbsp; 전체계좌조회")
        with st.container(border=True):
            st.markdown("💸&nbsp; ATM 출금")
    with c2:
        with st.container(border=True):
            if st.button("📊 금융상품", key="home_fp", use_container_width=True):
                go("financial_products")
                st.rerun()
        with st.container(border=True):
            st.markdown("🛡️&nbsp; 안전한 금융생활")

# ── 화면: 금융상품 ────────────────────────────────────────────────────────────
def screen_financial_products():
    menu_item("대출",         "loan",                 "💳")
    menu_item("퇴직연금",     "retirement_pension",   "📈")
    menu_item("외환",         "foreign_exchange",     "💱")
    menu_item("보험",         "insurance",            "🛡️")
    menu_item("펀드",         "fund",                 "📊")
    menu_item("신탁",         "trust",                "🏛️")
    menu_item("금융상품비교", "compare",              "⚖️")
    menu_item("영업점상품관", "branch_products",      "🏢")
    menu_item("스마트상담센터","smart_counsel",        "💬")

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
    st.success("✅ IRP 세액공제용 가입 화면에 도착했습니다.")

    with st.container(border=True):
        st.markdown("#### 개인형 IRP — 세액공제용")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("연간 납입 한도", "900만원")
        with c2:
            st.metric("세액공제율", "13.2 ~ 16.5%")
        st.caption("만 55세 이후 연금 형태로 수령 가능")

    st.markdown("#### 가입 전 필수 확인")
    chk1 = st.checkbox("투자 위험 등급 확인 (필수)")
    chk2 = st.checkbox("상품 설명서 확인 (필수)")
    chk3 = st.checkbox("적합성 진단 완료 (필수)")

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
def screen_investment_diagnosis():
    st.warning("⚠️ ETF·펀드 등 고위험 상품 이용 전 투자 성향 진단이 필요합니다.")

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
            st.success("✅ 투자 성향 진단이 완료되었습니다. 이제 운용 상품을 조회하실 수 있습니다.")

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

SCREEN_MAP = {
    "home":                 screen_home,
    "financial_products":   screen_financial_products,
    "retirement_pension":   screen_retirement_pension,
    "irp_new":              screen_irp_new,
    "irp_tax_saving":       screen_irp_tax_saving,
    "my_pension":           screen_my_pension,
    "portfolio":            screen_portfolio,
    "investment_diagnosis": screen_investment_diagnosis,
    "pension_design":       screen_pension_design,
}

# ── 동의 UI ───────────────────────────────────────────────────────────────────
def render_consent_ui():
    if not st.session_state.get("pending_route"):
        return

    st.markdown("---")
    with st.container(border=True):
        st.markdown(
            f'<div class="agent-bubble">🤖 &nbsp;{st.session_state["pending_consent"]}</div>',
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

# ── 에이전트 패널 ─────────────────────────────────────────────────────────────
def render_agent_panel():
    st.markdown("---")

    if st.session_state.get("agent_message"):
        st.markdown(
            f'<div class="agent-bubble">🤖 &nbsp;{st.session_state["agent_message"]}</div>',
            unsafe_allow_html=True,
        )

    with st.form("agent_input", clear_on_submit=True):
        user_input = st.text_input(
            "도우미",
            placeholder="🎤  무엇이 궁금하세요? (예: IRP 가입하고 싶어요)",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("전송 →", use_container_width=True)

    if submitted and user_input.strip():
        _handle_agent_response(user_input.strip())
        st.rerun()

def _handle_agent_response(user_input: str):
    result = navigate_ui(user_input)

    if result.get("type") == "navigation":
        st.session_state["pending_route"]   = result["route"]
        st.session_state["pending_consent"] = result["consent_message"]
        st.session_state["highlight_target"] = result.get("highlight_target")
        st.session_state["agent_message"]   = result["voice_guide"]

    elif result.get("status") == "hold":
        st.session_state["pending_route"]   = result["route"]
        st.session_state["pending_consent"] = result["voice_guide"]
        st.session_state["highlight_target"] = result.get("highlight_target")
        st.session_state["agent_message"]   = result["voice_guide"]

    elif result.get("type") == "suggestion":
        st.session_state["agent_message"]  = result["voice_guide"]
        st.session_state["pending_route"]  = None

    else:  # error
        st.session_state["agent_message"]  = result["voice_guide"]
        st.session_state["pending_route"]  = None

# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="NH 배리어프리 에이전트 데모",
        page_icon="🏦",
        layout="centered",
    )

    init_session()
    st.markdown(NH_CSS, unsafe_allow_html=True)

    render_header()

    route = st.session_state["current_route"]
    screen_fn = SCREEN_MAP.get(route, screen_home)
    screen_fn()

    render_consent_ui()
    render_agent_panel()


if __name__ == "__main__":
    main()
