import sys
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Add the experiment directory to sys.path to allow local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Assuming the main application files are in the root directory
from main import app, get_db
import models

# Setting up an isolated, in-memory SQLite database specifically for testing.
# StaticPool ensures that all async connections use the same in-memory database instance.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Creates a fresh database schema before each test and drops it afterward.
    This guarantees 100% isolation between tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncClient:
    """
    Overrides the main FastAPI database dependency to use the in-memory test database.
    Provides an asynchronous HTTP client to test endpoints.
    """
    async def override_get_db():
        yield db_session

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db

    # ASGITransport is the modern httpx standard for testing ASGI applications (FastAPI)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    # Clean up the override after the test finishes
    app.dependency_overrides.clear()