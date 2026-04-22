import streamlit as st

from frontend.components.streaming_handler import StreamingHandler


class ChatInterface:
    def __init__(self, api_client, session_id: str) -> None:
        self.api_client = api_client
        self.session_id = session_id
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def render_chat_history(self) -> None:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def handle_user_input(self) -> None:
        prompt = st.chat_input("Ask about weather, math, or search")
        if not prompt:
            return
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            content_placeholder = st.empty()
            status_placeholder = st.empty()
            handler = StreamingHandler(content_placeholder, status_placeholder)
            for event in self.api_client.stream_chat(prompt, self.session_id):
                handler.handle_event(event)
            assistant_text = handler.state.content.strip() or "No response."
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})

