"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
Zawiera konfigurację aplikacji, lifespan, migracje, logowanie oraz endpointy API.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import async_session, engine
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset
from exceptions import (
    FinanceException,
    AssetNotFoundException,
    DatabaseConnectionException,
)
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji:
    - tworzenie tabel
    - migracja SQLite (dodanie last_updated)
    """
    try:
        async with engine.begin() as conn:
            # Tworzenie tabel
            await conn.run_sync(Base.metadata.create_all)

            # Sprawdzenie struktury tabeli
            result = await conn.execute(
                text("PRAGMA table_info(financial_assets);")
            )
            columns = [row[1] for row in result.fetchall()]

            # Migracja: dodanie kolumny last_updated jeśli brak
            if "last_updated" not in columns:
                logger.info(
                    "Migracja: dodawanie kolumny last_updated do financial_assets"
                )

                await conn.execute(
                    text(
                        "ALTER TABLE financial_assets "
                        "ADD COLUMN last_updated DATETIME;"
                    )
                )

        logger.info(
            f"Uruchomienie systemu {settings.APP_NAME} "
            "(tabela financial_assets, PK: asset_id)"
        )

        yield

    finally:
        logger.info("Zamykanie aplikacji Finance Track")


# Inicjalizacja aplikacji
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator dostarczający sesję bazy danych.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@app.exception_handler(FinanceException)
async def finance_exception_handler(
    request: Request,
    exc: FinanceException,
) -> JSONResponse:
    """
    Obsługa wyjątków biznesowych.
    """
    logger.error(
        f"Błąd aplikacji (asset_id): {exc.detail} | URL: {request.url}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Obsługa błędów bazy danych.
    """
    logger.error(
        f"Błąd bazy danych (asset_id): {str(exc)} | URL: {request.url}"
    )

    db_exc = DatabaseConnectionException()

    return JSONResponse(
        status_code=db_exc.status_code,
        content={"detail": db_exc.detail},
    )


@app.get("/status")
async def healthcheck() -> dict:
    """
    Endpoint testowy sprawdzający status aplikacji.
    """
    return {
        "status": "ok",
        "database": "connected",
    }


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("ticker_symbol"),
    db: AsyncSession = Depends(get_db),
) -> List[FinancialAsset]:
    """
    Pobiera aktywa finansowe z filtrowaniem, paginacją i sortowaniem.
    """
    assets = await get_assets(
        db=db,
        skip=skip,
        limit=limit,
        min_price=min_price,
        sort_by=sort_by,
    )

    if not assets:
        raise AssetNotFoundException()

    logger.info("Pobrano listę aktywów z bazy danych")

    return assets


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(
    asset_in: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
) -> FinancialAsset:
    """
    Dodaje nowe aktywo finansowe.
    """
    asset = await create_asset(db, asset_in)

    logger.info(
        f"Dodano nowe aktywo (asset_id={asset.asset_id}, "
        f"ticker={asset.ticker_symbol})"
    )

    return asset