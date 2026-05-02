"""
Moduł odpowiedzialny za konfigurację bazy danych w systemie Finance Track.
Zastosowano asynchroniczną wersję SQLAlchemy 2.0+.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Konfiguracja asynchronicznego silnika dla SQLite
DATABASE_URL = "sqlite+aiosqlite:///finance.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def init_db():
    """
    Inicjalizacja bazy danych – asynchroniczne tworzenie tabel.
    Tworzy tabelę financial_assets (z kluczem głównym asset_id) jeśli nie istnieje.
    """
    from models import Base  # Import wewnątrz funkcji aby uniknąć cyklicznych importów

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✓ Baza danych została pomyślnie zainicjalizowana (tabela financial_assets z asset_id).")