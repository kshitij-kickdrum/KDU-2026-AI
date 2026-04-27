from __future__ import annotations

import streamlit as st


def render_status_display(status: str, error_message: str | None = None) -> None:
    if status == "pending":
        st.info("Status: Pending")
    elif status == "processing":
        st.warning("Status: Processing")
    elif status == "completed":
        st.success("Status: Completed")
    elif status == "failed":
        st.error("Status: Failed")
        if error_message:
            st.caption(error_message)
    else:
        st.write(f"Status: {status}")
