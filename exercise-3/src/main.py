from __future__ import annotations

import time
from typing import Any

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api/v1"


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=600)
    response.raise_for_status()
    return response.json()


def _init_state() -> None:
    defaults = {
        "session_id": None,
        "base_summary": None,
        "refined_summary": None,
        "input_word_count": 0,
        "qa_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


st.set_page_config(page_title="Tri-Model AI Assistant", layout="wide")
_init_state()

st.title("Tri-Model AI Assistant")
st.write("Summarize large text and ask questions with adaptive fallback Q&A.")

source_text = st.text_area("Input text", height=280, placeholder="Paste at least 100 characters")

if st.button("Generate Base Summary", type="primary"):
    if len(source_text.strip()) < 100:
        st.error("Text must be at least 100 characters.")
    else:
        with st.spinner("Generating base summary..."):
            start = time.perf_counter()
            try:
                data = _post("/summarize", {"text": source_text})
                st.session_state.session_id = data["session_id"]
                st.session_state.base_summary = data["base_summary"]
                st.session_state.refined_summary = None
                st.session_state.input_word_count = data["input_word_count"]
                st.success(f"Base summary generated in {time.perf_counter() - start:.2f}s")
            except Exception as exc:
                st.error(f"Summarization failed: {exc}")

if st.session_state.base_summary:
    st.subheader("Base Summary")
    st.write(st.session_state.base_summary)
    st.caption(f"Word count: {len(st.session_state.base_summary.split())}")

    choice = st.selectbox("Refinement preference", ["keep", "short", "medium", "long"], index=0)

    if choice != "keep" and st.button("Refine Summary"):
        with st.spinner("Refining summary..."):
            start = time.perf_counter()
            try:
                data = _post(
                    "/refine",
                    {
                        "base_summary": st.session_state.base_summary,
                        "length": choice,
                        "input_word_count": st.session_state.input_word_count,
                        "session_id": st.session_state.session_id,
                    },
                )
                st.session_state.refined_summary = data["refined_summary"]
                st.success(f"Refinement complete in {time.perf_counter() - start:.2f}s")
                st.caption(f"Compression ratio: {data['compression_ratio']:.3f}")
            except Exception as exc:
                st.error(f"Refinement failed: {exc}")

if st.session_state.refined_summary:
    st.subheader("Refined Summary")
    st.write(st.session_state.refined_summary)
    st.caption(f"Word count: {len(st.session_state.refined_summary.split())}")

if st.session_state.base_summary:
    st.subheader("Q&A")
    question = st.text_input("Ask a question", placeholder="Ask about the summary")
    if st.button("Get Answer") and question.strip():
        with st.spinner("Answering..."):
            try:
                data = _post(
                    "/qa",
                    {
                        "question": question,
                        "refined_summary": st.session_state.refined_summary,
                        "base_summary": st.session_state.base_summary,
                        "session_id": st.session_state.session_id,
                    },
                )
                st.session_state.qa_history.append({"question": question, "response": data})
            except Exception as exc:
                st.error(f"Q&A failed: {exc}")

    if st.session_state.qa_history:
        st.write("### Conversation")
        for idx, item in enumerate(reversed(st.session_state.qa_history), start=1):
            response = item["response"]
            st.markdown(f"**Q{idx}:** {item['question']}")
            if response.get("answer"):
                st.markdown(f"**A:** {response['answer']}")
                st.caption(
                    f"Confidence: {response['confidence']:.2f} | "
                    f"Fallback level: {response['fallback_level']} | "
                    f"Model: {response['model_used']}"
                )
            else:
                st.error(response.get("error", "Unable to answer"))
                if response.get("suggestion"):
                    st.info(response["suggestion"])
            with st.expander("Attempt details"):
                st.json(response.get("attempts", []))
