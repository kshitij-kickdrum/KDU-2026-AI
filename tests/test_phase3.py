import pytest


@pytest.mark.asyncio
async def test_phase3_happy_path(client) -> None:
    response = await client.post("/phase3/rerank", json={"query": "non surgery treatment"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["dense_top_k"]) > 0
    assert len(body["bm25_top_k"]) > 0
    assert len(body["merged_parents"]) > 0
    assert len(body["reranked_top_n"]) > 0


@pytest.mark.asyncio
async def test_phase3_top_n_gt_top_k_returns_400(client) -> None:
    response = await client.post("/phase3/rerank", json={"query": "x", "top_k": 2, "top_n": 3})
    assert response.status_code == 400
    assert response.json()["error"] == "top_n must be <= top_k"


@pytest.mark.asyncio
async def test_phase3_missing_query_returns_422(client) -> None:
    response = await client.post("/phase3/rerank", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_phase3_openai_failure(client, test_app) -> None:
    test_app.state.embedding_service.raise_provider = "openai"
    response = await client.post("/phase3/rerank", json={"query": "x"})
    assert response.status_code == 500
    assert response.json()["provider"] == "openai"
    test_app.state.embedding_service.raise_provider = None


@pytest.mark.asyncio
async def test_phase3_cohere_failure(client, test_app) -> None:
    test_app.state.rerank_service.raise_provider = "cohere"
    response = await client.post("/phase3/rerank", json={"query": "x"})
    assert response.status_code == 500
    assert response.json()["provider"] == "cohere"
    test_app.state.rerank_service.raise_provider = None


@pytest.mark.asyncio
async def test_phase3_reranked_top_n_length_property(client) -> None:
    response = await client.post("/phase3/rerank", json={"query": "x", "top_k": 5, "top_n": 2})
    assert response.status_code == 200
    assert len(response.json()["reranked_top_n"]) == 2
