import httpx
import streamlit as st

st.set_page_config(page_title="Embedding Retrieval System", layout="wide")
st.title("Embedding Retrieval System")

backend_url = st.sidebar.text_input("Backend URL", value="http://localhost:8000")

tab1, tab3 = st.tabs(["Phase 1: Compare", "Phase 3: Rerank"])


def show_http_error(prefix: str, exc: httpx.HTTPError) -> None:
    st.error(f"{prefix}: {exc}")
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            st.json(exc.response.json())
        except ValueError:
            st.code(exc.response.text)

with tab1:
    st.subheader("Phase 1 - Model Comparison")
    query = st.text_input("Query", key="phase1_query")
    if st.button("Run Phase 1", key="phase1_button"):
        if not query.strip():
            st.error("Query is required.")
        else:
            try:
                response = httpx.post(
                    f"{backend_url}/phase1/compare",
                    json={"query": query},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                st.write("Winner:", data["winner"])
                st.dataframe(data["scores"], use_container_width=True)
            except httpx.HTTPError as exc:
                show_http_error("Phase 1 request failed", exc)

with tab3:
    st.subheader("Phase 3 - Hybrid Retrieval + Rerank")
    query3 = st.text_input("Query", key="phase3_query")
    top_k = st.number_input("top_k", min_value=1, max_value=50, value=10, step=1)
    top_n = st.number_input("top_n", min_value=1, max_value=50, value=5, step=1)

    if st.button("Run Phase 3", key="phase3_button"):
        if not query3.strip():
            st.error("Query is required.")
        else:
            try:
                response = httpx.post(
                    f"{backend_url}/phase3/rerank",
                    json={"query": query3, "top_k": int(top_k), "top_n": int(top_n)},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                st.metric("Retrieval Latency (ms)", data["retrieval_latency_ms"])
                st.metric("Rerank Latency (ms)", data["rerank_latency_ms"])

                st.markdown("### Dense Top-K")
                st.dataframe(data["dense_top_k"], use_container_width=True)

                st.markdown("### BM25 Top-K")
                st.dataframe(data["bm25_top_k"], use_container_width=True)

                st.markdown("### Merged Parents")
                st.dataframe(data["merged_parents"], use_container_width=True)

                st.markdown("### Reranked Top-N")
                st.dataframe(data["reranked_top_n"], use_container_width=True)
            except httpx.HTTPError as exc:
                show_http_error("Phase 3 request failed", exc)
