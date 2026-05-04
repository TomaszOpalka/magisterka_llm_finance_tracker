"""
Konfiguracja asynchronicznego połączenia z bazą danych
dla systemu Finance Track.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings

# URL bazy danych pobierany z konfiguracji (config.py / .env)
DATABASE_URL = settings.DATABASE_URL

# Utworzenie asynchronicznego silnika bazy danych
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

# Fabryka sesji asynchronicznych
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)