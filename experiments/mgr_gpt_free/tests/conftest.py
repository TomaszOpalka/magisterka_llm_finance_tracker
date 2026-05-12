"""
Pytest configuration and async fixtures for Finance Track.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from experiments.mgr_gpt_free.main import app, get_db
from experiments.mgr_gpt_free.models import Base

# In-memory SQLite database for isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Async SQLAlchemy engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Async session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """
    Create and destroy database schema for tests.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide isolated async database session.
    """
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for endpoint testing.
    """

    async def override_get_db():
        yield db_session

    # Override production database dependency
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()