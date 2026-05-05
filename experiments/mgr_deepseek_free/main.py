"""
Główna aplikacja FastAPI systemu Finance Track.
Zarządza cyklem życia bazy danych, endpointami REST, logowaniem oraz obsługą wyjątków.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

# Lokalne importy
from database import engine, async_session
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset
from utils import logger
from exceptions import FinanceException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza zdarzeniami startu i zatrzymania aplikacji.
    Automatycznie tworzy tabele i wykonuje migrację (kolumna last_updated).
    """
    logger.info("Uruchomienie systemu Finance Track – inicjalizacja bazy danych.")

    async with engine.begin() as conn:
        # 1. Sprawdzenie / utworzenie tabeli financial_assets
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

        # 2. Migracja: dodanie kolumny last_updated, jeśli brak
        def column_exists(sync_conn, table_name, column_name):
            inspector = inspect(sync_conn)
            cols = [c["name"] for c in inspector.get_columns(table_name)]
            return column_name in cols

        has_last_updated = await conn.run_sync(
            column_exists, "financial_assets", "last_updated"
        )
        if not has_last_updated:
            logger.info(
                "Kolumna 'last_updated' nie istnieje – wykonuję ALTER TABLE."
            )
            await conn.execute(
                text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME")
            )
            logger.info("Kolumna 'last_updated' została dodana pomyślnie.")
        else:
            logger.info("Kolumna 'last_updated' już istnieje – migracja pominięta.")

    logger.info("System Finance Track wystartował pomyślnie.")
    yield

    await engine.dispose()
    logger.info("Zamknięcie systemu – silnik bazy danych wyłączony.")


# Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title="Finance Track",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------- HANDLERY WYJĄTKÓW ----------

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """
    Przechwytuje wszystkie wyjątki dziedziczące po FinanceException
    i zwraca ustandaryzowaną odpowiedź JSON z odpowiednim kodem statusu.
    """
    logger.error(
        f"Błąd biznesowy [{exc.status_code}]: {exc.detail} "
        f"(ścieżka: {request.url.path}, klucz zasobu: asset_id)"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Loguje standardowe wyjątki HTTP (np. 400, 401, 500) i przekazuje je dalej.
    """
    logger.error(
        f"HTTPException [{exc.status_code}]: {exc.detail} "
        f"(ścieżka: {request.url.path})"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ---------- ZALEŻNOŚCI ----------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Wstrzykiwanie zależności – generator asynchronicznej sesji.
    """
    async with async_session() as session:
        yield session


# ---------- ENDPOINTY ----------

@app.get(
    "/status",
    response_model=Dict[str, str],
    summary="Healthcheck systemu",
)
async def status():
    """Zwraca status aplikacji i łączności z bazą."""
    logger.info("Sprawdzenie statusu aplikacji – zdrowy.")
    return {"status": "ok", "database": "connected"}


@app.get(
    "/assets",
    response_model=List[FinancialAsset],
    summary="Pobierz aktywa z filtrowaniem, sortowaniem i paginacją",
)
async def read_assets(
    skip: int = Query(0, ge=0, description="Liczba rekordów do pominięcia"),
    limit: int = Query(10, ge=1, le=100, description="Maksymalna liczba rekordów (1-100)"),
    min_price: Optional[float] = Query(
        None, ge=0, description="Minimalna cena do filtrowania"
    ),
    sort_by: Optional[str] = Query(
        "ticker_symbol",
        description="Kolumna do sortowania (asset_id, ticker_symbol, last_price, market_cap, last_updated)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Zwraca listę aktywów z opcjonalnym pomijaniem, limitem, filtrem ceny i sortowaniem.
    W przypadku braku wyników zwracana jest pusta lista.
    """
    try:
        assets = await get_assets(
            skip=skip, limit=limit, min_price=min_price, sort_by=sort_by
        )
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