"""
Moduł odpowiedzialny za konfigurację bazy danych w systemie Finance Track.
Zastosowano asynchroniczną wersję SQLAlchemy 2.0+.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Konfiguracja asynchronicznego silnika dla SQLite
DATABASE_URL = "sqlite+aiosqlite:///finance.db"

# Tworzenie asynchronicznego silnika
engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # Ustaw na True podczas debugowania
    future=True
)

# Fabryka sesji asynchronicznych
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)