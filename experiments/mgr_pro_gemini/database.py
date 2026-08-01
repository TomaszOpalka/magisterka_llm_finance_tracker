from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

# Production-ready SQLite configuration with timeout for async concurrency
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./finance_track.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False, 
        "timeout": 15  # Prevents 'Database is locked' errors under high load
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()