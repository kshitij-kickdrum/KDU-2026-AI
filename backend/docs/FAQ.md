# FAQ

## Do I need cloud hosting?
No. This project is configured for local execution only.

## Is VirusTotal required?
No. It is disabled by default in local-only mode.

## Which LLM is used?
OpenRouter `openai/gpt-4o-mini` as configured in `config/config.yaml`.

## Can I use only PDFs?
Yes. URL ingestion is optional.

## Why do sources repeat?
Sources are deduplicated now; if you still see repeats, clear chat and ask again.

## How to back up my local data?
Use pipeline backup method or copy `backend/data/metadata.db`.

