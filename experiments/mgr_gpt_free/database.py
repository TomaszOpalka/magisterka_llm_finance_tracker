"""
Konfiguracja asynchronicznego połączenia z bazą danych SQLite
dla systemu Finance Track.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# URL połączenia do bazy SQLite (asynchroniczny sterownik aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///./finance.db"

# Utworzenie asynchronicznego silnika bazy danych
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Ustaw na True w celu debugowania zapytań SQL
)

# Fabryka sesji asynchronicznych
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Zapobiega wygasaniu obiektów po commit
)