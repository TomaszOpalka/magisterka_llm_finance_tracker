"""
Main FastAPI application for Finance Track system.
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
from crud import (
    get_assets,
    create_asset,
    update_all_assets_prices,
    get_asset_by_ticker,
)
from exceptions import (
    FinanceException,
    AssetNotFoundException,
    DatabaseConnectionException,
)
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            result = await conn.execute(
                text("PRAGMA table_info(financial_assets);")
            )
            columns = [row[1] for row in result.fetchall()]

            if "last_updated" not in columns:
                await conn.execute(
                    text(
                        "ALTER TABLE financial_assets "
                        "ADD COLUMN last_updated DATETIME;"
                    )
                )

        logger.info(f"{settings.APP_NAME} started (PK: asset_id)")

        yield

    finally:
        logger.info("Application shutdown")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    """
    async with async_session() as session:
        yield session


@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    logger.error(f"Finance error (asset_id): {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error (asset_id): {str(exc)}")
    db_exc = DatabaseConnectionException()

    return JSONResponse(
        status_code=db_exc.status_code,
        content={"detail": db_exc.detail},
    )


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("ticker_symbol"),
    db: AsyncSession = Depends(get_db),
):
    assets = await get_assets(db, skip, limit, min_price, sort_by)

    if not assets:
        raise AssetNotFoundException()

    return assets


@app.get("/assets/{ticker_symbol}", response_model=FinancialAsset)
async def read_asset(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    asset = await get_asset_by_ticker(db, ticker_symbol)

    if not asset:
        raise AssetNotFoundException()

    return asset


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(
    asset_in: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_asset(db, asset_in)


@app.post("/assets/sync")
async def sync_prices(db: AsyncSession = Depends(get_db)):
    updated = await update_all_assets_prices(db)

    return {
        "status": "success",
        "updated_records": updated,
    }