# Architecture Decision Matrix

## Scenario A - Offline Mobile Application
- Recommended Model/Provider: HuggingFace `all-MiniLM-L6-v2`
- Rationale: Runs fully offline with low memory footprint at 384 dimensions.
- Key Trade-offs: Lower semantic accuracy than larger cloud models.

## Scenario B - Large-Scale E-Commerce (500M Documents)
- Recommended Model/Provider: OpenAI `text-embedding-3-small` plus binary quantization
- Rationale: Strong quality with practical memory usage after bit packing.
- Key Trade-offs: Quantization can reduce retrieval precision for edge queries.

## Scenario C - Legal Discovery Platform
- Recommended Model/Provider: Voyage AI `voyage-law-2` plus Cohere reranking
- Rationale: Domain-tuned embeddings and reranking improve precision on legal text.
- Key Trade-offs: Higher latency and multi-provider cost.

## Scenario D - Multilingual SaaS Platform
- Recommended Model/Provider: OpenAI `text-embedding-3-large`
- Rationale: Broad multilingual support in one embedding space.
- Key Trade-offs: High dimensional vectors increase storage and cost.

## Scenario E - Multimodal System (Text + Image)
- Recommended Model/Provider: CLIP-family approach for shared text-image space
- Rationale: Enables cross-modal retrieval workflows.
- Key Trade-offs: Requires additional image preprocessing and infrastructure.

## Cross-Scenario Summary

| Scenario | Provider | Model | Dims | Compression | Reranking |
|---|---|---|---|---|---|
| Offline Mobile | HuggingFace | all-MiniLM-L6-v2 | 384 | None | None |
| E-Commerce 500M | OpenAI | text-embedding-3-small | 1536 -> 192B | Binary | None |
| Legal Discovery | Voyage AI | voyage-law-2 | 1024 | None | Cohere |
| Multilingual SaaS | OpenAI | text-embedding-3-large | 3072 | Matryoshka 256 | Optional |
| Multimodal | OpenAI/CLIP | CLIP ViT-L/14 | 768 | None | None |
