import streamlit as st

from components.chat_interface import ChatInterface
from components.usage_metrics import UsageMetrics
from utils.api_client import APIClient
from utils.session_manager import get_session_id


def main() -> None:
    st.set_page_config(page_title="Multi-Function AI Assistant", layout="wide")
    st.title("Multi-Function AI Assistant")

    api_client = APIClient()
    session_id = get_session_id()

    usage_component = UsageMetrics()
    usage_data = api_client.get_usage_stats(session_id=session_id, detailed=False)
    usage_component.render(usage_data)

    chat = ChatInterface(api_client=api_client, session_id=session_id)
    chat.render_chat_history()
    chat.handle_user_input()


if __name__ == "__main__":
    main()

