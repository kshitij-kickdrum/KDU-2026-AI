from __future__ import annotations

import time
from collections.abc import Iterator

import streamlit as st

from src.ui.components.cost_display import render_cost_display
from src.ui.components.status_display import render_status_display


STAGE_LABELS = {
    "queued": "Queued",
    "extract": "Extracting or transcribing content",
    "summary": "Generating summary",
    "embed": "Creating embeddings",
    "persist": "Saving transcript and metadata",
    "done": "Done",
    "failed": "Failed",
}

STAGE_PROGRESS = {
    "queued": 5,
    "extract": 30,
    "summary": 55,
    "embed": 80,
    "persist": 95,
    "done": 100,
    "failed": 100,
}


def _stream_words(text: str, delay_seconds: float = 0.01) -> Iterator[str]:
    for word in text.split():
        yield f"{word} "
        time.sleep(delay_seconds)


def render_upload_page(file_manager, processing_manager, cost_tracker) -> None:
    st.header("Upload & Process")
    uploaded = st.file_uploader("Upload file", type=["pdf", "jpg", "jpeg", "png", "mp3", "wav"])

    if uploaded is None:
        st.session_state.pop("upload_signature", None)
        st.session_state.pop("upload_response", None)
        st.caption("Upload a file to start processing.")
        return

    signature = (uploaded.name, int(getattr(uploaded, "size", 0)))
    if st.session_state.get("upload_signature") != signature:
        try:
            response = file_manager.upload_file(uploaded)
        except Exception as exc:
            st.error(f"Upload failed: {exc}")
            return
        st.session_state["upload_signature"] = signature
        st.session_state["upload_response"] = {
            "file_id": response.file_id,
            "display_id": getattr(response, "display_id", response.file_id),
            "filename": response.filename,
            "file_type": response.file_type,
        }
    else:
        cached = st.session_state.get("upload_response")
        if not cached:
            st.error("Upload state missing. Please reselect the file.")
            return
        response = type("UploadResp", (), cached)()

    st.success(f"Uploaded: {response.filename}")
    public_id = getattr(response, "display_id", response.file_id)
    st.caption(f"File ID: {public_id}")

    if st.button("Process File", key="process_uploaded_file"):
        progress_bar = st.progress(0)
        with st.status("Processing file...", expanded=True) as status:
            try:
                def on_stage(stage: str) -> None:
                    label = STAGE_LABELS.get(stage, stage)
                    progress = STAGE_PROGRESS.get(stage, 0)
                    progress_bar.progress(progress)
                    status.write(label)

                result = processing_manager.process_file(response.file_id, on_stage=on_stage)
                status.update(label="Processing complete", state="complete")

                st.subheader("Transcript Preview")
                st.text_area(
                    "Transcript",
                    value=result.get("transcript_preview", ""),
                    height=220,
                    key=f"transcript_preview_{response.file_id}",
                )

                st.subheader("Summary")
                st.write_stream(_stream_words(result["summary"]))

                st.subheader("Key Points")
                for point in result["key_points"]:
                    st.markdown(f"- {point}")

                st.subheader("Tags")
                st.write(", ".join(result["topic_tags"]) if result["topic_tags"] else "No tags generated")

                summary = cost_tracker.get_cost_summary(file_id=response.file_id)
                render_cost_display(summary)
            except Exception as exc:
                status.update(label="Processing failed", state="error")
                st.error(f"Processing failed: {exc}")

    status = file_manager.get_file_status(response.file_id)
    render_status_display(status.processing_status, status.error_message)
