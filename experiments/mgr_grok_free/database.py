"""
Moduł odpowiedzialny za konfigurację bazy danych w systemie Finance Track.
Zastosowano asynchroniczną wersję SQLAlchemy 2.0+.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings


# Użycie DATABASE_URL z centralnej konfiguracji
engine = create_async_engine(
    settings.DATABASE_URL,
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

    print(f"✓ Baza danych została pomyślnie zainicjalizowana ({settings.DATABASE_URL})")