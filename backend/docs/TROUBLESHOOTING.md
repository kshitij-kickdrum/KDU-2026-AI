# Troubleshooting

## Streamlit starts but answers are weak
- Cause: embedding model download blocked.
- Symptom: logs mention fallback hash embeddings.
- Fix: allow access to Hugging Face or pre-download `all-MiniLM-L6-v2`.

## URL rejected as not allowed
- Cause: domain whitelist in `config/config.yaml`.
- Fix: add domain under `document_processing.allowed_domains`, then click "Reload Config" or restart app.

## `no_context` warnings
- Cause: retrieved chunks filtered too hard or low query coverage.
- Fix: increase `Top-K`, reduce `semantic_weight` bias, and ask with specific keywords.

## Temporary PDF paths showing in sources
- Fix: re-ingest PDFs after latest updates; original upload filename is now preserved.

## Pytest permission errors on Windows (`WinError 5`)
- Cause: temporary/cache folder locks.
- Workaround: run smaller suites (`tests/unit`) and close other tools holding file handles.

