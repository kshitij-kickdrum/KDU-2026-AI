import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.session import get_db_session
from app.users.models import User, UserRole
from app.core.security import hash_password

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_template_test"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionFactory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def init_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionFactory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:
    async def override_db():
        yield db

    app.dependency_overrides[get_db_session] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        email="user@example.com",
        password_hash=hash_password("Pass@1234"),
        full_name="Test User",
        role=UserRole.user,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("Pass@1234"),
        full_name="Test Admin",
        role=UserRole.admin,
    )
    db.add(admin)
    await db.flush()
    return admin


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "Pass@1234",
    })
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "Pass@1234",
    })
    return response.json()["access_token"]
