from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from database import engine
from models import Base
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji + migracja SQLite.
    """
    try:
        async with engine.begin() as conn:
            # Tworzenie tabel jeśli nie istnieją
            await conn.run_sync(Base.metadata.create_all)

            # Sprawdzenie czy kolumna last_updated istnieje
            result = await conn.execute(
                text("PRAGMA table_info(financial_assets);")
            )
            columns = [row[1] for row in result.fetchall()]

            # Jeśli brak kolumny → wykonaj migrację
            if "last_updated" not in columns:
                logger.info(
                    "Migracja bazy: dodawanie kolumny last_updated do financial_assets"
                )

                await conn.execute(
                    text(
                        "ALTER TABLE financial_assets "
                        "ADD COLUMN last_updated DATETIME;"
                    )
                )

        logger.info(
            "System uruchomiony poprawnie (PK: asset_id, migracje OK)"
        )

        yield

    finally:
        logger.info("Zamykanie aplikacji")