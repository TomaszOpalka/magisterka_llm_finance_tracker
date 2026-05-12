"""
Pytest fixtures for the Finance Track test suite.
Uses an in-memory SQLite database (shared cache) to ensure isolation from production.
Overrides the FastAPI dependency injection to use the test database.
"""

import sys
import os
import asyncio
from typing import AsyncIterator
import httpx
import pytest

# Add the experiment directory to sys.path to allow local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Import the FastAPI app and the dependency to override
from main import app, get_db
from models import Base

# Test database URL – shared in-memory database that survives connection changes
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared"

# Create the test engine and session factory
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


# Override the get_db dependency to use the test session
async def override_get_db() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    Required by pytest-asyncio for session-scoped async fixtures.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def init_db():
    """
    Session-scoped fixture: creates all tables before tests,
    and drops them after all tests finish.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def cleanup_db(init_db):
    """
    Function-scoped fixture: clears all rows from financial_assets
    before each test to guarantee isolation.
    """
    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM financial_assets"))
    yield


@pytest.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    Provides an HTTP client that communicates with our FastAPI app
    using ASGI transport, without needing a running server.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client