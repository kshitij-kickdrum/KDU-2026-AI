import pytest


@pytest.mark.asyncio
async def test_phase1_happy_path(client) -> None:
    response = await client.post(
        "/phase1/compare",
        json={"query": "The person was sweating heavily with a fast heart rate"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["scores"]) == 3
    assert body["winner"] == "voyage-4-lite"


@pytest.mark.asyncio
async def test_phase1_missing_query_returns_422(client) -> None:
    response = await client.post("/phase1/compare", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_phase1_openai_failure(client, test_app) -> None:
    test_app.state.embedding_service.raise_provider = "openai"
    response = await client.post("/phase1/compare", json={"query": "text"})
    assert response.status_code == 500
    assert response.json()["provider"] == "openai"
    test_app.state.embedding_service.raise_provider = None


@pytest.mark.asyncio
async def test_phase1_voyage_failure(client, test_app) -> None:
    test_app.state.embedding_service.raise_provider = "voyageai"
    response = await client.post("/phase1/compare", json={"query": "text"})
    assert response.status_code == 500
    assert response.json()["provider"] == "voyageai"
    test_app.state.embedding_service.raise_provider = None


@pytest.mark.asyncio
async def test_phase1_hf_failure(client, test_app) -> None:
    test_app.state.embedding_service.raise_provider = "huggingface"
    response = await client.post("/phase1/compare", json={"query": "text"})
    assert response.status_code == 500
    assert response.json()["provider"] == "huggingface"
    test_app.state.embedding_service.raise_provider = None


@pytest.mark.asyncio
async def test_phase1_winner_consistency_property(client) -> None:
    response = await client.post("/phase1/compare", json={"query": "check winner"})
    body = response.json()
    best = max(body["scores"], key=lambda item: item["cosine_similarity"])
    assert body["winner"] == best["model"]


@pytest.mark.asyncio
async def test_phase1_scores_list_completeness_property(client) -> None:
    response = await client.post("/phase1/compare", json={"query": "check scores"})
    body = response.json()
    models = {entry["model"] for entry in body["scores"]}
    assert models == {
        "text-embedding-3-small",
        "voyage-4-lite",
        "all-MiniLM-L6-v2",
    }
