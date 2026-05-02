"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
Zawiera obsługę wyjątków biznesowych oraz logowanie.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, engine
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset
from utils import logger
from exceptions import (
    FinanceException,
    AssetNotFoundException,
    DatabaseConnectionException,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(
            "Uruchomienie systemu Finance Track - baza gotowa "
            "(tabela financial_assets, PK: asset_id)"
        )

        yield

    finally:
        logger.info("Zamykanie aplikacji Finance Track")


app = FastAPI(
    title="Finance Track API",
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator sesji bazy danych.
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
    Globalny handler dla wyjątków biznesowych.
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
    Endpoint testowy.
    """
    return {
        "status": "ok",
        "database": "connected",
    }


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(
    db: AsyncSession = Depends(get_db),
) -> List[FinancialAsset]:
    """
    Pobiera wszystkie aktywa finansowe.
    """
    assets = await get_assets(db)

    # Jeśli brak danych → wyjątek biznesowy
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