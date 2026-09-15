"""
BF Agent 관리자 보드 — 로컬 전용
실행: streamlit run admin_demo/admin_app.py
"""

import streamlit as st
from pathlib import Path
import datetime

from utils.kb_utils import (
    list_domains,
    list_files,
    read_file,
    save_file,
    create_file,
    delete_file,
    update_index,
)
from utils.pdf_utils import pdf_to_markdown
from utils.agent_runner import AgentChat

KNOWLEDGE_BASE = Path(__file__).parent.parent / "data" / "knowledge"

# 에이전트 채팅 인스턴스 (모듈 로드 시 1회 생성)
@st.cache_resource
def get_agent_chats():
    from app.customer_management_agent import customer_management_agent
    from app.system_improvement_agent import system_improvement_agent
    return {
        "customer": AgentChat(customer_management_agent, "admin", "chat_customer"),
        "curator": AgentChat(system_improvement_agent, "curator", "chat_curator"),
    }

st.set_page_config(page_title="BF Agent 관리자", page_icon="🛠️", layout="wide")
st.title("🛠️ BF Agent 관리자 보드")
st.caption("로컬 전용 — 지식베이스 관리 / PDF 업로드 / 갱신 이력 / 에이전트")

tab_kb, tab_upload, tab_log, tab_customer, tab_curator = st.tabs([
    "📚 지식베이스", "📄 PDF 업로드", "📋 갱신 이력",
    "👤 고객 관리 에이전트", "🧹 스킬 큐레이터",
])


# ── 탭 1: 지식베이스 에디터 ─────────────────────────────────────────────────
with tab_kb:
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("파일 목록")
        domain = st.selectbox("도메인", list_domains(KNOWLEDGE_BASE))
        files = list_files(KNOWLEDGE_BASE / domain)

        selected = st.radio(
            "파일 선택",
            files,
            format_func=lambda f: f.name,
        ) if files else None

        st.divider()
        st.markdown("**새 파일 생성**")
        new_name = st.text_input("파일명 (확장자 제외)", placeholder="예: 금리인하효과")
        if st.button("생성", disabled=not new_name or not domain):
            path = create_file(KNOWLEDGE_BASE / domain, new_name, domain)
            update_index(KNOWLEDGE_BASE, domain, path.stem)
            st.success(f"{path.name} 생성됨")
            st.rerun()

        if selected:
            st.divider()
            if st.button("🗑️ 파일 삭제", type="secondary"):
                delete_file(selected, KNOWLEDGE_BASE)
                st.warning(f"{selected.name} 삭제됨 — index.md에서 수동 제거 필요")
                st.rerun()

    with col_right:
        if selected:
            st.subheader(f"편집: `{selected.name}`")
            content = read_file(selected)
            edited = st.text_area("내용", content, height=520, label_visibility="collapsed")

            col_save, col_llm = st.columns([1, 1])
            with col_save:
                if st.button("💾 저장", type="primary"):
                    save_file(selected, edited)
                    st.success("저장 완료")
            with col_llm:
                st.button("✨ LLM 정리 (미구현)", disabled=True, help="추후 구현 예정")
        else:
            st.info("왼쪽에서 파일을 선택하거나 새 파일을 생성하세요.")


# ── 탭 2: PDF 업로드 ────────────────────────────────────────────────────────
with tab_upload:
    st.subheader("PDF → 지식베이스 변환")
    st.caption("PDF를 업로드하면 텍스트를 추출해 마크다운으로 변환합니다.")

    upload_domain = st.selectbox("저장할 도메인", list_domains(KNOWLEDGE_BASE), key="upload_domain")
    uploaded = st.file_uploader("PDF 파일 선택", type="pdf")

    if uploaded:
        with st.spinner("변환 중..."):
            md_content = pdf_to_markdown(uploaded, upload_domain)

        st.markdown("**변환 미리보기**")
        edited_md = st.text_area("내용 검토 후 저장", md_content, height=400)

        save_name = st.text_input("저장할 파일명 (확장자 제외)", value=Path(uploaded.name).stem)
        if st.button("📥 지식베이스에 저장", type="primary", disabled=not save_name):
            path = KNOWLEDGE_BASE / upload_domain / f"{save_name}.md"
            path.write_text(edited_md, encoding="utf-8")
            update_index(KNOWLEDGE_BASE, upload_domain, save_name)
            st.success(f"`{upload_domain}/{save_name}.md` 저장 완료")


# ── 탭 3: 갱신 이력 ─────────────────────────────────────────────────────────
with tab_log:
    st.subheader("갱신 이력 (wiki_admin/log.md)")

    log_path = KNOWLEDGE_BASE / "wiki_admin" / "log.md"
    log_content = read_file(log_path) if log_path.exists() else "# 이력 없음\n"

    col_log, col_action = st.columns([2, 1])

    with col_log:
        edited_log = st.text_area("이력", log_content, height=400, label_visibility="collapsed")
        if st.button("💾 이력 저장"):
            save_file(log_path, edited_log)
            st.success("이력 저장됨")

    with col_action:
        st.markdown("**수동 갱신 트리거**")
        st.caption("정형 정보를 직접 수동으로 기록합니다.")

        with st.form("manual_update"):
            update_type = st.selectbox("갱신 항목", ["기준금리", "예금금리", "세액공제한도", "기타"])
            update_note = st.text_area("변경 내용", height=100)
            submitted = st.form_submit_button("기록 추가")

        if submitted and update_note:
            today = datetime.date.today().isoformat()
            entry = f"\n## {today} — {update_type}\n{update_note}\n"
            new_log = log_content + entry
            save_file(log_path, new_log)
            st.success("이력에 추가됨")
            st.rerun()

        st.divider()
        st.markdown("**lint 리포트**")
        lint_path = KNOWLEDGE_BASE / "wiki_admin" / "lint_report.md"
        if lint_path.exists():
            with st.expander("최근 lint 결과 보기"):
                st.markdown(read_file(lint_path))
        else:
            st.caption("lint_report.md 없음")


def _render_chat_tab(chat: AgentChat, state_key: str, placeholder_cmds: list[str]):
    """공통 채팅 UI."""
    col_chat, col_hint = st.columns([3, 1])

    with col_hint:
        st.markdown("**빠른 명령**")
        for cmd in placeholder_cmds:
            if st.button(cmd, key=f"btn_{state_key}_{cmd}"):
                with st.spinner("처리 중..."):
                    chat.send(st.session_state, cmd)
                st.rerun()
        st.divider()
        if st.button("🔄 대화 초기화", key=f"reset_{state_key}"):
            chat.reset(st.session_state)
            st.rerun()

    with col_chat:
        history = chat.history(st.session_state)
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(msg["text"])

        user_input = st.chat_input("관리자 명령을 입력하세요")
        if user_input:
            with st.spinner("처리 중..."):
                chat.send(st.session_state, user_input)
            st.rerun()


# ── 탭 4: 고객 관리 에이전트 ─────────────────────────────────────────────────
with tab_customer:
    st.subheader("👤 고객 관리 에이전트")
    st.caption("사용자 프로필 조회·삭제·통계 (`memory/users/`)")
    try:
        chats = get_agent_chats()
        _render_chat_tab(
            chats["customer"],
            "customer",
            ["사용자 목록 보고해줘", "통계 분포 보여줘", "스킬 현황 보고해줘"],
        )
    except Exception as e:
        st.error(f"에이전트 로드 실패: {e}")
        st.caption("`.env` 파일과 `GOOGLE_API_KEY` 설정을 확인하세요.")


# ── 탭 5: 스킬 큐레이터 ──────────────────────────────────────────────────────
with tab_curator:
    st.subheader("🧹 스킬 큐레이터")
    st.caption("에이전트 스킬 문서 정리·병합·압축 (`memory/agents/`)")
    try:
        chats = get_agent_chats()
        _render_chat_tab(
            chats["curator"],
            "curator",
            ["큐레이션 현황 보여줘", "전체 정리해줘", "이력 보여줘"],
        )
    except Exception as e:
        st.error(f"에이전트 로드 실패: {e}")
        st.caption("`.env` 파일과 `GOOGLE_API_KEY` 설정을 확인하세요.")
