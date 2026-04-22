import streamlit as st


class UsageMetrics:
    def render(self, usage: dict) -> None:
        st.sidebar.subheader("Usage")
        if not usage:
            st.sidebar.info("No usage data yet.")
            return
        st.sidebar.metric("Requests", usage.get("requests_count", 0))
        st.sidebar.metric("Total Tokens", usage.get("total_tokens", 0))
        st.sidebar.metric("Cost (USD)", f"{usage.get('total_cost', 0):.6f}")
        st.sidebar.caption(
            f"LLM input tokens: {usage.get('total_input_tokens', 0)} | "
            f"LLM output tokens: {usage.get('total_output_tokens', 0)}"
        )
        tools = usage.get("tools_used", [])
        st.sidebar.write("Tools used:", ", ".join(tools) if tools else "None")
