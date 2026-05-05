from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from config.settings import Settings
from storage.faiss_store import FAISSStore


DOCS = [
    {
        "doc_id": "kb-001",
        "title": "How to update billing information",
        "content_preview": "To update billing information, open account settings, choose billing, and replace the payment method before the next invoice date.",
        "source": "knowledge_base",
        "created_at": "2026-01-01T00:00:00Z",
    },
    {
        "doc_id": "kb-002",
        "title": "Overdue payment policy",
        "content_preview": "Accounts marked overdue keep access for a short grace period. Paying the outstanding balance restores current status automatically.",
        "source": "policy",
        "created_at": "2026-01-01T00:00:00Z",
    },
    {
        "doc_id": "faq-001",
        "title": "Invoice copy request",
        "content_preview": "Customers can request invoice copies by email address or customer ID. Billing support can resend the latest invoice.",
        "source": "faq",
        "created_at": "2026-01-01T00:00:00Z",
    },
]


def main() -> None:
    settings = Settings.load(require_api_keys=False)
    settings.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {str(i): doc for i, doc in enumerate(DOCS)}
    settings.faiss_metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    try:
        import faiss

        vectors = np.vstack(
            [FAISSStore.embed(f"{doc['title']} {doc['content_preview']}") for doc in DOCS]
        )
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        faiss.write_index(index, str(settings.faiss_index_path))
        print(f"Built FAISS index at {settings.faiss_index_path}")
    except Exception as exc:
        print(f"Wrote metadata fallback only; FAISS unavailable: {exc}")


if __name__ == "__main__":
    main()

