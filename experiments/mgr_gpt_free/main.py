"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
Zawiera konfigurację lifespan, inicjalizację bazy danych oraz logowanie.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, engine
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji (startup/shutdown).
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
    Generator dostarczający sesję bazy danych.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Globalna obsługa wyjątków HTTP z logowaniem.
    """
    logger.error(
        f"Błąd HTTP {exc.status_code} przy żądaniu {request.url}: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
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
    db: AsyncSession = Depends(get_db),
) -> List[FinancialAsset]:
    """
    Pobiera wszystkie aktywa finansowe.
    """
    try:
        assets = await get_assets(db)
        logger.info("Pobrano listę aktywów z bazy danych")
        return assets

    except SQLAlchemyError as exc:
        logger.error(f"Błąd bazy danych podczas pobierania aktywów: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Błąd podczas pobierania danych",
        )


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(
    asset_in: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
) -> FinancialAsset:
    """
    Dodaje nowe aktywo finansowe.
    """
    try:
        asset = await create_asset(db, asset_in)

        logger.info(
            f"Dodano nowe aktywo (asset_id={asset.asset_id}, "
            f"ticker={asset.ticker_symbol})"
        )

        return asset

    except SQLAlchemyError as exc:
        logger.error(f"Błąd bazy danych podczas zapisu aktywa: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Błąd podczas zapisu danych",
        )