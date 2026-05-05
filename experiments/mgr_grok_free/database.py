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
    Inicjalizacja i migracja bazy danych.
    Tworzy tabele oraz dodaje brakującą kolumnę last_updated (SQLite).
    """
    from models import Base

    # async with engine.begin() as conn:
    #     # Tworzenie tabel
    #     await conn.run_sync(Base.metadata.create_all)

    #     # Migracja: dodanie kolumny last_updated jeśli nie istnieje
    #     try:
    #         # Sprawdzenie istnienia kolumny
    #         result = await conn.execute(
    #             text("PRAGMA table_info(financial_assets)")
    #         )
    #         columns = [row[1] for row in result.fetchall()]
            
    #         if "last_updated" not in columns:
    #             await conn.execute(
    #                 text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME")
    #             )
    #             logger.info("Migracja wykonana: dodano kolumnę last_updated")
    #         else:
    #             logger.info("Kolumna last_updated już istnieje")
    #     except Exception as mig_error:
    #         logger.warning(f"Problem podczas migracji kolumny: {mig_error}")

    # print("✓ Baza danych została pomyślnie zainicjalizowana (asset_id jako klucz główny).")