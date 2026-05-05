"""
Main FastAPI application for Finance Track system.
Production-ready with error resilience.
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
from services import StockServiceException
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    """
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


@app.exception_handler(StockServiceException)
async def stock_service_exception_handler(
    request: Request,
    exc: StockServiceException,
):
    """
    Global handler for stock service errors.
    """
    logger.error(f"Stock service error: {str(exc)}")

    return JSONResponse(
        status_code=503,
        content={"detail": "Stock data service unavailable"},
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
    """
    Synchronize all asset prices with resilience.
    """
    from models import FinancialAsset
    from sqlalchemy import select
    from services import get_stock_price
    from datetime import datetime

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