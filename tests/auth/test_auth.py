import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Pass@1234",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "Pass@1234",
        "full_name": "Duplicate",
    })
    assert response.status_code == 409
    assert response.json()["code"] == "USER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "weak",
        "full_name": "Weak Pass",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Pass@1234",
        "full_name": "Bad Email",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "Pass@1234",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "WrongPass@1",
    })
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "Pass@1234",
    })
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"
