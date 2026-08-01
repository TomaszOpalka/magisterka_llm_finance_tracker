"""
Finance Track API.

Production asynchronous financial tracking system.
Supports PR #67 camelCase API contract while keeping
internal database fields in snake_case.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from crud import create_asset
from crud import get_asset_by_ticker
from crud import get_assets
from crud import update_all_assets_prices
from database import AsyncSessionLocal
from database import engine
from exceptions import AssetNotFoundException
from exceptions import FinanceException
from models import Base
from models import FinancialAsset
from schemas import FinancialAsset
from schemas import FinancialAssetCreate
from schemas import AnalyticsResponse
from utils import logger


BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_PATH = (
    BASE_DIR /
    "templates" /
    "dashboard.html"
)


DEFAULT_ASSETS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "TSLA",
    "META",
    "BTC-USD",
    "ETH-USD",
    "SPY",
]


async def seed_default_assets():
    """
    Insert default financial assets into an empty database.
    """

    async with AsyncSessionLocal() as session:

        result = await session.execute(
            select(FinancialAsset)
        )

        existing_assets = result.scalars().all()

        if existing_assets:
            logger.info(
                "Database already contains assets"
            )
            return

        for ticker in DEFAULT_ASSETS:

            asset = FinancialAsset(
                asset_id=str(uuid4()),
                ticker_symbol=ticker,
                current_market_price=0.0,
                market_cap=0,
            )

            session.add(asset)

        await session.commit()

        logger.info(
            "Inserted %s default financial assets",
            len(DEFAULT_ASSETS),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    """

    try:

        async with engine.begin() as connection:

            await connection.run_sync(
                Base.metadata.create_all
            )

        await seed_default_assets()

        logger.info(
            "Finance Track API started"
        )

        logger.info(
            "Primary key verification: asset_id"
        )

        yield

    except Exception as error:

        logger.error(
            "Startup failure: %s",
            error,
        )

        raise


app = FastAPI(
    title="Finance Track API",
    version="1.0.0",
    description=(
        "Asynchronous financial tracking API "
        "built with FastAPI and SQLAlchemy 2.0. "
        "PR #67 introduces camelCase API contracts "
        "while preserving internal snake_case "
        "database architecture."
    ),
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    """
    Provide asynchronous database sessions.
    """

    async with AsyncSessionLocal() as session:
        yield session


@app.exception_handler(FinanceException)
async def finance_exception_handler(
    request: Request,
    exc: FinanceException,
):
    """
    Handle application exceptions.
    """

    logger.error(
        "Finance error: %s",
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
    )


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def dashboard():
    """
    Return Cosmic UI dashboard.
    """

    if not DASHBOARD_PATH.exists():

        raise HTTPException(
            status_code=404,
            detail="Dashboard template missing",
        )

    return HTMLResponse(
        content=DASHBOARD_PATH.read_text(
            encoding="utf-8",
        )
    )


@app.get("/status")
async def status():
    """
    Return system health information.
    """

    return {
        "status": "ok",
        "database": "connected",
    }


@app.get(
    "/assets",
)
async def read_assets(
    db: AsyncSession = Depends(get_db),
):
    """
    Return all tracked assets.
    """

    assets = await get_assets(
        db=db,
        limit=100,
    )

    return assets


@app.post(
    "/assets",
)
async def add_asset(
    payload: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new financial asset.
    """

    return await create_asset(
        db=db,
        asset=payload,
    )


@app.post("/assets/sync")
async def sync_assets(
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronize market prices.
    """

    try:

        updated = await update_all_assets_prices(
            db=db,
        )

        return {
            "status": "completed",
            "updatedAssets": updated,
        }

    except TimeoutError:

        raise HTTPException(
            status_code=502,
            detail="External market provider timeout",
        )

    except Exception as error:

        logger.error(
            "Synchronization failed: %s",
            error,
        )

        raise HTTPException(
            status_code=502,
            detail="Market synchronization failed",
        )


@app.get(
    "/assets/{ticker_symbol}",
)
async def get_single_asset(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve one asset by ticker.
    """

    asset = await get_asset_by_ticker(
        db=db,
        ticker_symbol=ticker_symbol,
    )

    if asset is None:

        raise AssetNotFoundException(
            detail="Asset not found",
        )

    return asset