import uuid

import streamlit as st


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"sess_{uuid.uuid4().hex[:16]}"
    return st.session_state.session_id

