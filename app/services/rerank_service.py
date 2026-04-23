import cohere

from app.config import Settings
from app.models.schemas import ParentContext, RankedDoc
from app.services.errors import ProviderAPIError


class RerankService:
    def __init__(self, settings: Settings) -> None:
        self._client = cohere.AsyncClient(api_key=settings.cohere_api_key)

    async def rerank(
        self,
        query: str,
        parent_docs: list[ParentContext],
        top_n: int,
    ) -> list[RankedDoc]:
        docs_text = [doc.text for doc in parent_docs]
        dense_rank_by_parent = {doc.parent_id: idx + 1 for idx, doc in enumerate(parent_docs)}
        try:
            response = await self._client.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=docs_text,
                top_n=top_n,
            )
        except Exception as exc:
            raise ProviderAPIError(
                provider="cohere",
                status_code=500,
                message="Rerank failed",
                detail=str(exc),
            ) from exc

        results: list[RankedDoc] = []
        for item in response.results:
            parent = parent_docs[item.index]
            results.append(
                RankedDoc(
                    doc_id=parent.parent_id,
                    text=parent.text,
                    relevance_score=float(item.relevance_score),
                    original_dense_rank=dense_rank_by_parent[parent.parent_id],
                )
            )
        return results
