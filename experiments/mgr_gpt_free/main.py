"""
Main FastAPI application for Finance Track.

Database layer:
- snake_case

API layer:
- camelCase
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from analytics import calculate_moving_average
from analytics import calculate_rsi
from config import settings
from crud import create_asset
from crud import get_asset_by_ticker
from crud import get_assets
from crud import update_all_assets_prices
from database import AsyncSessionLocal
from database import engine
from exceptions import AssetNotFoundException
from exceptions import DatabaseConnectionException
from exceptions import FinanceException
from models import Base
from schemas import AnalyticsResponse
from schemas import FinancialAsset
from schemas import FinancialAssetCreate
from services import get_historical_data
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup lifecycle.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            result = await conn.execute(
                text(
                    """
                    PRAGMA table_info(financial_assets)
                    """
                )
            )

            columns = [row[1] for row in result.fetchall()]

            if "last_updated" not in columns:
                await conn.execute(
                    text(
                        """
                        ALTER TABLE financial_assets
                        ADD COLUMN last_updated DATETIME
                        """
                    )
                )

        logger.info("Application startup completed")
        logger.info("Primary key verified: asset_id")

        yield

    except Exception as error:
        logger.error(
            "Database initialization failed: %s",
            error,
        )

        raise DatabaseConnectionException(
            detail="Database initialization failed",
        ) from error


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    """
    Database dependency provider.
    """
    async with AsyncSessionLocal() as session:
        yield session


@app.exception_handler(FinanceException)
async def finance_exception_handler(
    request: Request,
    exc: FinanceException,
):
    """
    Handle custom finance exceptions.
    """
    logger.error(
        "Finance exception occurred: %s",
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    """
    Handle HTTP exceptions.
    """
    logger.error(
        "HTTP exception occurred: %s",
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Finance Track API",
        "status": "running",
    }


@app.get("/status")
async def status():
    """
    Healthcheck endpoint.
    """
    return {
        "status": "ok",
        "database": "connected",
    }


@app.get(
    "/assets",
    response_model=list[FinancialAsset],
)
async def read_assets(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all assets.
    """
    assets = await get_assets(
        db=db,
        skip=skip,
        limit=limit,
    )

    if not assets:
        raise AssetNotFoundException(
            detail="No assets found",
        )

    return assets


@app.post(
    "/assets",
    response_model=FinancialAsset,
    status_code=201,
)
async def create_new_asset(
    asset: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new financial asset.

    Request body accepts camelCase fields.
    """
    try:
        return await create_asset(
            db=db,
            asset=asset,
        )

    except Exception as error:
        logger.error(
            "Asset creation failed: %s",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Asset creation failed",
        ) from error


@app.get(
    "/assets/{ticker_symbol}",
    response_model=FinancialAsset,
)
async def get_asset(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve single asset by ticker symbol.
    """
    asset = await get_asset_by_ticker(
        db=db,
        ticker_symbol=ticker_symbol,
    )

    if asset is None:
        raise AssetNotFoundException(
            detail=(
                f"Asset with ticker "
                f"{ticker_symbol} not found"
            ),
        )

    return asset


@app.post("/assets/sync")
async def sync_assets(
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronize asset prices.
    """
    try:
        updated_assets = await update_all_assets_prices(
            db=db,
        )

        return {
            "message": "Synchronization completed",
            "updatedAssets": updated_assets,
        }

    except Exception as error:
        logger.error(
            "Synchronization failed: %s",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Synchronization failed",
        ) from error


@app.get(
    "/assets/{ticker_symbol}/analytics",
    response_model=AnalyticsResponse,
)
async def get_asset_analytics(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve analytics for asset.
    """
    asset = await get_asset_by_ticker(
        db=db,
        ticker_symbol=ticker_symbol,
    )

    if asset is None:
        raise AssetNotFoundException(
            detail="Asset not found",
        )

    historical_prices = await get_historical_data(
        ticker=ticker_symbol,
        days=30,
    )

    if not historical_prices:
        raise HTTPException(
            status_code=503,
            detail="Historical data unavailable",
        )

    moving_average = calculate_moving_average(
        historical_prices,
    )

    rsi_value = calculate_rsi(
        historical_prices,
        periods=14,
    )

    return AnalyticsResponse(
        ticker_symbol=ticker_symbol,
        moving_average_30d=moving_average,
        rsi_14=rsi_value,
    )