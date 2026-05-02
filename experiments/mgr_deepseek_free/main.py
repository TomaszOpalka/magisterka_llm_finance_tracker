"""
Główna aplikacja FastAPI systemu Finance Track.
Zarządza cyklem życia bazy danych, endpointami REST oraz logowaniem zdarzeń.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect

# Lokalne importy
from database import engine, async_session
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset
from utils import logger  # Import polskiego loggera


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza zdarzeniami startu i zatrzymania aplikacji.
    Przy starcie tworzy tabele (jeśli nie istnieją) oraz loguje uruchomienie.
    """
    # --- STARTUP ---
    logger.info("Uruchomienie systemu Finance Track – inicjalizacja bazy danych.")

    async with engine.begin() as conn:
        def check_tables_exist(sync_conn):
            inspector = inspect(sync_conn)
            return "financial_assets" in inspector.get_table_names()

        table_exists = await conn.run_sync(check_tables_exist)
        if not table_exists:
            await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "Utworzono tabelę 'financial_assets' (klucz główny: asset_id)."
            )
        else:
            logger.info("Tabela 'financial_assets' już istnieje – pomijam tworzenie.")

    logger.info("System Finance Track wystartował pomyślnie.")
    yield  # Aplikacja działa

    # --- SHUTDOWN ---
    await engine.dispose()
    logger.info("Zamknięcie systemu – silnik bazy danych wyłączony.")


# Inicjalizacja FastAPI z lifespanem
app = FastAPI(
    title="Finance Track",
    version="0.1.0",
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Wstrzykiwanie zależności – generator asynchronicznej sesji.
    Sesja automatycznie zamykana po obsłużeniu żądania.
    """
    async with async_session() as session:
        yield session


# ---------- HEALTHCHECK ----------
@app.get(
    "/status",
    response_model=Dict[str, str],
    summary="Healthcheck systemu",
)
async def status():
    """Zwraca status aplikacji i łączności z bazą."""
    logger.info("Sprawdzenie statusu aplikacji – zdrowy.")
    return {"status": "ok", "database": "connected"}


# ---------- ENDPOINTY CRUD ----------
@app.get(
    "/assets",
    response_model=List[FinancialAsset],
    summary="Pobierz wszystkie aktywa finansowe",
)
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Zwraca listę wszystkich rekordów z tabeli financial_assets.
    """
    try:
        assets = await get_assets()
        logger.info(f"Pobrano listę aktywów – liczba rekordów: {len(assets)}")
        return assets
    except Exception as e:
        logger.error(f"Błąd pobierania aktywów: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania aktywów: {str(e)}"
        )


@app.post(
    "/assets",
    response_model=FinancialAsset,
    status_code=201,
    summary="Dodaj nowy aktyw finansowy",
)
async def create_new_asset(
    asset_data: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Tworzy nowy wpis aktywu. Klucz główny `asset_id` generowany automatycznie (UUID).
    """
    try:
        new_asset = await create_asset(asset_data)
        logger.info(
            f"Dodano nowe aktywo: {new_asset.asset_id} "
            f"(symbol: {new_asset.ticker_symbol})"
        )
        return new_asset
    except ValueError as e:
        logger.warning(f"Konflikt podczas dodawania aktywa: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd przy dodawaniu aktywa: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Nieoczekiwany błąd: {str(e)}"
        )