"""Pytest fixtures and configuration for PromptIQ test suite."""

import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test configuration
os.environ["PROMPTIQ_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["MANAGED_INFERENCE_PRIMARY_ROUTE"] = "mock"

from sqlalchemy.pool import StaticPool

from promptiq.api.main import app
from promptiq.core.database import Base, get_db
from promptiq.core.security import create_access_token
from promptiq.schemas.auth import UserCreate
from promptiq.services.auth_service import AuthService

# In-memory SQLite async engine for tests
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides an isolated database session per test with fresh schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Provides an asynchronous HTTP test client wired to the in-memory test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Provisions a primary test user and default workspace."""
    user, ws = await AuthService.register_user(
        db_session,
        UserCreate(email="alice@example.com", password="Password123!", full_name="Alice Engineer"),
    )
    return user, ws


@pytest_asyncio.fixture(scope="function")
async def user_auth_headers(test_user):
    """Returns Bearer authorization headers for the primary test user."""
    user, _ = test_user
    token = create_access_token({"sub": user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def second_test_user(db_session: AsyncSession):
    """Provisions a secondary test user for multi-tenancy tests."""
    user, ws = await AuthService.register_user(
        db_session,
        UserCreate(email="bob@example.com", password="Password123!", full_name="Bob Security"),
    )
    return user, ws


@pytest_asyncio.fixture(scope="function")
async def second_auth_headers(second_test_user):
    """Returns Bearer authorization headers for the secondary test user."""
    user, _ = second_test_user
    token = create_access_token({"sub": user.id})
    return {"Authorization": f"Bearer {token}"}
