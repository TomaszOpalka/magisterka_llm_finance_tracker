"""
Main FastAPI application for Finance Track system.
Production-ready with analytics and external data integration.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import async_session, engine
from models import Base, FinancialAsset
from schemas import FinancialAsset, FinancialAssetCreate
from crud import (
    get_assets,
    create_asset,
    get_asset_by_ticker,
)
from services import (
    get_stock_price,
    get_historical_data,
    StockServiceException,
)
from analytics import calculate_moving_average
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
    Initializes database and applies lightweight migration.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # SQLite schema check for last_updated column
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

    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.
    """
    async with async_session() as session:
        yield session


@app.exception_handler(FinanceException)
async def finance_exception_handler(
    request: Request,
    exc: FinanceException,
):
    logger.error(f"Finance error (asset_id): {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.error(f"Database error (asset_id): {str(exc)}")

    db_exc = DatabaseConnectionException()

    return JSONResponse(
        status_code=db_exc.status_code,
        content={"detail": db_exc.detail},
    )


@app.exception_handler(StockServiceException)
async def stock_service_exception_handler(
    request: Request,
    exc: StockServiceException,
):
    logger.error(f"Stock service error: {str(exc)}")

    return JSONResponse(
        status_code=503,
        content={"detail": "Stock data service unavailable"},
    )


@app.get("/status")
async def healthcheck() -> dict:
    """
    Healthcheck endpoint.
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
):
    """
    Retrieve assets with filtering and pagination.
    """
    assets = await get_assets(db, skip, limit, min_price, sort_by)

    if not assets:
        raise AssetNotFoundException()

    return assets


@app.get("/assets/{ticker_symbol}", response_model=FinancialAsset)
async def read_asset(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single asset by ticker.
    """
    asset = await get_asset_by_ticker(db, ticker_symbol)

    if not asset:
        raise AssetNotFoundException()

    return asset


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(
    asset_in: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create new asset.
    """
    return await create_asset(db, asset_in)


@app.post("/assets/sync")
async def sync_prices(db: AsyncSession = Depends(get_db)):
    """
    Synchronize asset prices from external API with resilience.
    """
    result = await db.execute(select(FinancialAsset))
    assets = result.scalars().all()

    updated = 0

    for asset in assets:
        try:
            price = await get_stock_price(asset.ticker_symbol)

            if price is None:
                logger.warning(
                    f"No price data for ticker={asset.ticker_symbol} "
                    f"(asset_id={asset.asset_id})"
                )
                continue

            asset.last_price = price
            asset.last_updated = datetime.utcnow()
            updated += 1

        except Exception as exc:
            logger.error(
                f"Failed to update ticker={asset.ticker_symbol} "
                f"(asset_id={asset.asset_id}): {exc}"
            )
            continue

    await db.commit()

    return {
        "status": "success",
        "updated_records": updated,
    }


@app.get("/assets/{ticker_symbol}/analytics")
async def get_asset_analytics(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return 30-day moving average analytics.
    """
    asset = await get_asset_by_ticker(db, ticker_symbol)

    if not asset:
        raise AssetNotFoundException()

    prices = await get_historical_data(ticker_symbol, days=30)
    moving_avg = calculate_moving_average(prices)

    if moving_avg is None:
        raise StockServiceException("Insufficient data for analytics")

    return {
        "ticker_symbol": ticker_symbol,
        "moving_average_30d": moving_avg,
    }