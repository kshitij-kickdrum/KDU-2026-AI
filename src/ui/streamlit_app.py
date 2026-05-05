from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.orchestration_engine import OrchestrationEngine

st.set_page_config(page_title="AgentKit Orchestration", layout="wide")


@st.cache_resource
def get_engine() -> OrchestrationEngine:
    return OrchestrationEngine()


engine = get_engine()


STATE_LABELS = {
    "active": "Ready",
    "requires_user_input": "Needs More Information",
    "completed": "Completed",
}

FIELD_LABELS = {
    "account_holder_name": "Account holder name",
    "account_number": "Account number",
    "routing_number": "Routing number",
    "cvv": "CVV",
    "amount": "Amount",
    "card_number": "Card number",
    "expiration_date": "Expiration date",
}


def masked_session_id(session_id: str | None) -> str:
    if not session_id:
        return "New conversation"
    return f"Session ...{session_id[-6:]}"


def field_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name.replace("_", " ").title())


if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Session")
    st.caption(masked_session_id(st.session_state.session_id))
    if st.button("New Session", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    if st.session_state.session_id:
        session = engine.memory.load_session(st.session_state.session_id)
        st.metric("Status", STATE_LABELS.get(session["state"], "Working"))
        st.metric("Tokens", session["token_count"])
        st.subheader("Case Facts")
        if session["case_facts"]:
            st.json(session["case_facts"])
        else:
            st.caption("No stored case facts yet.")
        if session.get("missing_fields"):
            st.subheader("Missing Fields")
            for missing_field in session["missing_fields"]:
                st.write(f"- {field_label(missing_field)}")

st.title("AgentKit Orchestration")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask the coordinator, ingest a document, or use /plan for planner-executor")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    result = engine.process_query(prompt, st.session_state.session_id)
    st.session_state.session_id = result["session_id"]
    st.session_state.messages.append({"role": "assistant", "content": result["response"]})
    with st.chat_message("assistant"):
        st.write(result["response"])
    st.rerun()
