"""
Finance Track - Main FastAPI application.

Architecture:
- Database layer: snake_case (SQLAlchemy)
- API layer: camelCase (Pydantic aliasing)
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from analytics import calculate_moving_average, calculate_rsi
from config import settings
from crud import (
    create_asset,
    get_asset_by_ticker,
    get_assets,
    update_all_assets_prices,
)
from database import AsyncSessionLocal, engine
from exceptions import (
    AssetNotFoundException,
    DatabaseConnectionException,
    FinanceException,
)
from models import Base
from schemas import (
    AnalyticsResponse,
    FinancialAsset,
    FinancialAssetCreate,
)
from services import get_historical_data
from utils import logger


# =========================
# Lifespan
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]

            if "last_updated" not in columns:
                await conn.execute(
                    text(
                        "ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"
                    )
                )

        logger.info("Application started successfully")
        logger.info("Database initialized with assetId primary key")

        yield

    except Exception as e:
        logger.error("Startup failure: %s", e)
        raise DatabaseConnectionException("Database init failed") from e


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


# =========================
# DB Dependency
# =========================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# =========================
# Exception Handlers
# =========================

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    logger.error("Finance error: %s", exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP error: %s", exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# =========================
# Healthcheck
# =========================

@app.get("/status")
async def status():
    return {"status": "ok", "database": "connected"}


# =========================
# Assets CRUD
# =========================

@app.get("/assets", response_model=list[FinancialAsset])
async def read_assets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100),
    db: AsyncSession = Depends(get_db),
):
    assets = await get_assets(db=db, skip=skip, limit=limit)

    if not assets:
        raise AssetNotFoundException("No assets found")

    return assets


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def create_new_asset(
    asset: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_asset(db=db, asset=asset)


@app.get("/assets/{ticker_symbol}", response_model=FinancialAsset)
async def get_asset(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    asset = await get_asset_by_ticker(db=db, ticker_symbol=ticker_symbol)

    if not asset:
        raise AssetNotFoundException(f"Asset {ticker_symbol} not found")

    return asset


# =========================
# Sync prices (yfinance)
# =========================

@app.post("/assets/sync")
async def sync_assets(db: AsyncSession = Depends(get_db)):
    try:
        updated = await update_all_assets_prices(db=db)

        return {
            "message": "Sync completed",
            "updated_assets": updated,
        }

    except Exception as e:
        logger.error("Sync failed: %s", e)
        raise HTTPException(status_code=500, detail="Sync failed")


# =========================
# Analytics endpoint
# =========================

@app.get(
    "/assets/{ticker_symbol}/analytics",
    response_model=AnalyticsResponse,
)
async def analytics(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    asset = await get_asset_by_ticker(db, ticker_symbol)

    if not asset:
        raise AssetNotFoundException("Asset not found")

    history = await get_historical_data(ticker_symbol, days=30)

    if not history:
        raise HTTPException(status_code=503, detail="No market data")

    return AnalyticsResponse(
        ticker_symbol=ticker_symbol,
        moving_average_30d=calculate_moving_average(history),
        rsi_14=calculate_rsi(history),
    )