from __future__ import annotations

import json

import pandas as pd
import streamlit as st

STATUS_BADGES = {
    "pending": "🕒 Pending",
    "processing": "🟡 Processing",
    "completed": "✅ Completed",
    "failed": "🔴 Failed",
}


def render_library_page(db, json_storage, file_manager, processing_manager) -> None:
    st.header("Library")

    c1, c2 = st.columns(2)
    file_type = c1.selectbox("File type", ["all", "pdf", "image", "audio"])
    status = c2.selectbox("Status", ["all", "pending", "processing", "completed", "failed"])
    q = st.text_input("Search by filename")

    files = db.list_files(
        file_type=None if file_type == "all" else file_type,
        status=None if status == "all" else status,
        name_query=q or None,
    )

    if not files:
        st.info("No files found")
        return

    df = pd.DataFrame(files)[["display_id", "filename", "file_type", "upload_timestamp", "processing_status"]]
    df = df.sort_values(by="upload_timestamp", ascending=False)
    st.dataframe(df, use_container_width=True)

    selected_file_id = st.selectbox(
        "Select file",
        [f["file_id"] for f in files],
        format_func=lambda fid: next(
            (
                f"{x.get('display_id', 'FILE')} - {x['filename']}"
                for x in files
                if x["file_id"] == fid
            ),
            fid,
        ),
    )
    row = db.get_file(selected_file_id)
    if not row:
        return

    st.subheader(row["filename"])
    st.caption(
        f"ID: {row.get('display_id', '-')}"
        f" | Type: {row['file_type']}"
        f" | Status: {STATUS_BADGES.get(row['processing_status'], row['processing_status'])}"
    )

    a, b = st.columns(2)
    if a.button("Reprocess", key=f"reprocess_{selected_file_id}"):
        with st.status("Reprocessing file...", expanded=True) as status_box:
            try:
                processing_manager.process_file(
                    selected_file_id,
                    on_stage=lambda stage: status_box.write(stage.replace("_", " ").title()),
                )
                status_box.update(label="Reprocessing complete", state="complete")
                st.success("File reprocessed")
                st.rerun()
            except Exception as exc:
                status_box.update(label="Reprocessing failed", state="error")
                st.error(f"Reprocessing failed: {exc}")

    if b.button("Delete", key=f"delete_{selected_file_id}"):
        try:
            file_manager.delete_file(selected_file_id)
            st.success("File deleted")
            st.rerun()
        except Exception as exc:
            st.error(f"Delete failed: {exc}")

    st.write("Summary")
    st.write(row.get("summary") or "Not available")

    key_points = []
    topic_tags = []
    if row.get("key_points"):
        key_points = json.loads(row["key_points"])
    if row.get("topic_tags"):
        topic_tags = json.loads(row["topic_tags"])

    if key_points:
        st.write("Key Points")
        for point in key_points:
            st.write(f"- {point}")
    if topic_tags:
        st.write("Tags")
        st.write(", ".join(topic_tags))

    if row.get("transcript_path"):
        try:
            transcript = json_storage.load_transcript(selected_file_id)
            st.write("Transcript")
            st.text_area("Transcript text", transcript["transcript"].get("cleaned_text", ""), height=300)
        except FileNotFoundError:
            st.warning("Transcript file missing on disk")

    cost = db.get_cost_breakdown(file_id=selected_file_id)
    st.write(f"File cost: ${cost['total_cost_usd']:.6f}")
