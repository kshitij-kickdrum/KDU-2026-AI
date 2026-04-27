from __future__ import annotations

import html
import re

import streamlit as st


def _highlight(text: str, query: str) -> str:
    words = [w for w in re.split(r"\W+", query.strip()) if len(w) >= 2]
    if not words:
        return html.escape(text)
    pattern = "(" + "|".join(re.escape(w) for w in words[:8]) + ")"
    escaped = html.escape(text)
    return re.sub(pattern, r"<mark>\1</mark>", escaped, flags=re.IGNORECASE)


def render_search_page(search_manager, db) -> None:
    st.header("Semantic Search")
    query = st.text_input("Search query")
    top_k = st.slider("Top K", 1, 20, 5)

    completed_files = [f for f in db.list_files(status="completed")]
    filter_ids = st.multiselect(
        "Filter by files",
        options=[f["file_id"] for f in completed_files],
        format_func=lambda fid: next(
            (
                f"{x.get('display_id', 'FILE')} - {x['filename']}"
                for x in completed_files
                if x["file_id"] == fid
            ),
            fid,
        ),
    )

    if st.button("Search"):
        if not query.strip():
            st.warning("Enter a query")
            return

        with st.spinner("Searching..."):
            response = search_manager.semantic_search(query, top_k=top_k, file_ids=filter_ids or None)

        st.caption(f"Query cost: ${response.query_cost_usd:.8f} | tokens: {response.query_tokens_used}")
        if not response.results:
            st.info("No results found")
            return

        for result in response.results:
            with st.container(border=True):
                st.markdown(
                    f"**{result.filename}** ({result.file_type}) | score: `{result.similarity_score}` | chunk: `{result.chunk_index}`"
                )
                full_context = f"{result.context_before}{result.chunk_text}{result.context_after}"
                highlighted = _highlight(full_context, query)
                preview = full_context[:600]
                preview_highlighted = _highlight(preview, query)

                st.markdown(preview_highlighted, unsafe_allow_html=True)
                if len(full_context) > 600:
                    with st.expander("Show full context"):
                        st.markdown(highlighted, unsafe_allow_html=True)
