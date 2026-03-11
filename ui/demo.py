import streamlit as st
import sys
import os

# app 디렉토리를 경로에 추가하여 에이전트 호출 가능하게 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Barrier-Free Agent", page_icon="♿")

st.title("👵 Barrier-Free 금융 비서")
st.subheader("노년층과 초보 투자자를 위한 NH농협 서비스 안내")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("무엇을 도와드릴까요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # TODO: app.agent.get_agent()를 통한 응답 생성 로직 연결
        response = f"'{prompt}'에 대한 답변입니다. (에이전트 연결 필요)"
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
