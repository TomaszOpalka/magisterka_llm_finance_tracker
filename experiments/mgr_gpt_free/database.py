"""
Asynchronous database configuration for Finance Track.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings

# Database URL loaded from environment configuration
DATABASE_URL = settings.DATABASE_URL

# Async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

# Async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

AsyncSessionLocal = async_session