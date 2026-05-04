from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from src.models.file_models import EmbeddingRecord
from src.services.audio_transcriber import AudioTranscriber
from src.services.cost_tracker import CostTracker
from src.services.embedding_generator import EmbeddingGenerator
from src.services.summary_generator import SummaryGenerator
from src.services.vision_processor import VisionProcessor
from src.storage.database import Database
from src.storage.json_storage import JsonStorage
from src.storage.vector_store import VectorStore


class ProcessingManager:
    def __init__(
        self,
        db: Database,
        json_storage: JsonStorage,
        vector_store: VectorStore,
        vision_processor: VisionProcessor,
        audio_transcriber: AudioTranscriber,
        summary_generator: SummaryGenerator,
        embedding_generator: EmbeddingGenerator,
        cost_tracker: CostTracker,
    ) -> None:
        self.db = db
        self.json_storage = json_storage
        self.vector_store = vector_store
        self.vision_processor = vision_processor
        self.audio_transcriber = audio_transcriber
        self.summary_generator = summary_generator
        self.embedding_generator = embedding_generator
        self.cost_tracker = cost_tracker

    def process_file(
        self,
        file_id: str,
        on_stage: Callable[[str], None] | None = None,
    ) -> dict:
        row = self.db.get_file(file_id)
        if row is None:
            raise ValueError(f"File not found: {file_id}")

        def _emit(stage: str) -> None:
            if on_stage:
                on_stage(stage)

        _emit("queued")
        self.db.update_file_status(file_id, "processing")

        try:
            file_type = row["file_type"]
            file_path = row["file_path"]

            _emit("extract")
            if file_type == "audio":
                transcription = self.audio_transcriber.transcribe_audio(file_path)
                raw_text = transcription.text
                extraction_method = "whisper-local"
            elif file_type == "pdf":
                extracted = self.vision_processor.extract_text_from_pdf(file_path)
                raw_text = extracted.text
                extraction_method = "gpt-4o-mini-vision"
                self.cost_tracker.log_api_call(
                    operation_type="vision",
                    model_name="gpt-4o-mini",
                    input_tokens=extracted.tokens_used.input_tokens,
                    output_tokens=extracted.tokens_used.output_tokens,
                    file_id=file_id,
                    metadata={"stage": "vision_extraction"},
                )
            else:
                extracted = self.vision_processor.extract_text_from_image(file_path)
                raw_text = extracted.text
                extraction_method = "gpt-4o-mini-vision"
                self.cost_tracker.log_api_call(
                    operation_type="vision",
                    model_name="gpt-4o-mini",
                    input_tokens=extracted.tokens_used.input_tokens,
                    output_tokens=extracted.tokens_used.output_tokens,
                    file_id=file_id,
                    metadata={"stage": "vision_extraction"},
                )

            _emit("summary")
            summary = self.summary_generator.generate_summary(raw_text)
            self.cost_tracker.log_api_call(
                operation_type="llm",
                model_name="gpt-4o-mini",
                input_tokens=summary.tokens_used.input_tokens,
                output_tokens=summary.tokens_used.output_tokens,
                file_id=file_id,
                metadata={"stage": "summary"},
            )

            _emit("embed")
            embedding_response = self.embedding_generator.create_embeddings(raw_text)
            self.cost_tracker.log_api_call(
                operation_type="embedding",
                model_name="text-embedding-3-small",
                input_tokens=embedding_response.tokens_used,
                output_tokens=0,
                file_id=file_id,
                metadata={"stage": "embedding"},
            )

            # Allow reprocessing same file by replacing previous chunk rows.
            self.db.delete_embeddings_for_file(file_id)

            embedding_ids = [str(uuid4()) for _ in embedding_response.chunks]
            file_ids = [file_id] * len(embedding_response.chunks)
            chunk_indices = [chunk.chunk_index for chunk in embedding_response.chunks]

            faiss_ids = self.vector_store.add_vectors(
                vectors=embedding_response.embeddings,
                embedding_ids=embedding_ids,
                file_ids=file_ids,
                chunk_indices=chunk_indices,
            )

            records: list[EmbeddingRecord] = []
            for i, chunk in enumerate(embedding_response.chunks):
                records.append(
                    EmbeddingRecord(
                        embedding_id=embedding_ids[i],
                        file_id=file_id,
                        chunk_index=chunk.chunk_index,
                        chunk_text=chunk.text,
                        chunk_start_char=chunk.start_char,
                        chunk_end_char=chunk.end_char,
                        faiss_index_id=faiss_ids[i],
                    )
                )
            self.db.insert_embeddings(records)

            _emit("persist")
            transcript_payload = {
                "file_id": file_id,
                "filename": row["filename"],
                "file_type": file_type,
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "transcript": {
                    "raw_text": raw_text,
                    "cleaned_text": raw_text.strip(),
                    "metadata": {
                        "word_count": len(raw_text.split()),
                        "language": "auto",
                        "extraction_method": extraction_method,
                    },
                },
                "chunks": [
                    {
                        "chunk_index": c.chunk_index,
                        "text": c.text,
                        "start_char": c.start_char,
                        "end_char": c.end_char,
                        "word_count": len(c.text.split()),
                    }
                    for c in embedding_response.chunks
                ],
            }

            transcript_path = self.json_storage.save_transcript(file_id, transcript_payload)
            self.db.update_file_results(
                file_id=file_id,
                transcript_path=transcript_path,
                summary=summary.summary,
                key_points=summary.key_points,
                topic_tags=summary.topic_tags,
            )
            _emit("done")

            preview = raw_text.strip()
            return {
                "file_id": file_id,
                "status": "completed",
                "summary": summary.summary,
                "key_points": summary.key_points,
                "topic_tags": summary.topic_tags,
                "transcript_path": transcript_path,
                "transcript_preview": preview[:3000],
            }
        except Exception as exc:
            _emit("failed")
            self.db.update_file_status(file_id, "failed", error_message=str(exc))
            raise
