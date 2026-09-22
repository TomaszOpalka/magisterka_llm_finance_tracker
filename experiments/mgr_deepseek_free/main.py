"""
Production‑ready FastAPI application for Finance Track API v1.0.0.
Implements async endpoints, camelCase contract (PR #67), automatic seeding,
and serves the Cosmic UI dashboard.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import inspect, text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine, async_session
from models import Base, FinancialAsset
from schemas import (
    FinancialAsset as FinancialAssetSchema,
    FinancialAssetCreate,
    AnalyticsResponse,
)
from crud import (
    get_assets,
    create_asset,
    update_all_assets_prices,
    get_asset_by_ticker,
)
from services import get_historical_data
from analytics import calculate_moving_average, calculate_rsi
from utils import logger
from exceptions import (
    FinanceException,
    AssetNotFoundException,
    AnalyticsException,
)

# Default tickers for seeding
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "TSLA", "META", "BTC-USD", "ETH-USD", "SPY",
]


async def seed_default_assets():
    """
    Seeds the database with 10 default financial assets if the table is empty.
    All assets are created with placeholder prices (0.0) ready for sync.
    """
    async with async_session() as session:
        # Check if any assets exist
        result = await session.execute(select(func.count()).select_from(FinancialAsset))
        count = result.scalar()
        if count > 0:
            logger.info("Database already contains assets – skipping seeding.")
            return

        logger.info("Empty database detected. Seeding 10 default assets...")
        for ticker in DEFAULT_TICKERS:
            asset = FinancialAsset(
                asset_id=str(uuid.uuid4()),
                ticker_symbol=ticker,
                current_market_price=0.0,
                market_cap=0,
                last_updated=None,
            )
            session.add(asset)
        await session.commit()
        logger.info(f"Seeded {len(DEFAULT_TICKERS)} default assets successfully.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: creates tables, performs light migration,
    seeds default data if necessary, and disposes the engine on shutdown.
    """
    logger.info("Starting Finance Track API – initializing database.")

    async with engine.begin() as conn:
        # Create tables if missing
        def check_tables_exist(sync_conn):
            inspector = inspect(sync_conn)
            return "financial_assets" in inspector.get_table_names()

        table_exists = await conn.run_sync(check_tables_exist)
        if not table_exists:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Created table 'financial_assets' (primary key: asset_id).")
        else:
            logger.info("Table 'financial_assets' already exists – skipping creation.")

        # Migration: add last_updated column if missing
        def column_exists(sync_conn, table_name, column_name):
            inspector = inspect(sync_conn)
            cols = [c["name"] for c in inspector.get_columns(table_name)]
            return column_name in cols

        has_last_updated = await conn.run_sync(
            column_exists, "financial_assets", "last_updated"
        )
        if not has_last_updated:
            logger.info("Column 'last_updated' missing – executing ALTER TABLE.")
            await conn.execute(
                text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME")
            )
            logger.info("Column 'last_updated' added successfully.")
        else:
            logger.info("Column 'last_updated' already exists – migration skipped.")

    # Seed default data if table is empty
    await seed_default_assets()

    logger.info("Finance Track API started successfully.")
    yield

    await engine.dispose()
    logger.info("Shutting down – database engine disposed.")


app = FastAPI(
    title="Finance Track API",
    version="1.0.0",
    description=(
        "Asynchronous financial asset tracker with camelCase JSON contract. "
        "Built with FastAPI, SQLAlchemy 2.0 (async), and Pydantic v2. "
        "This API provides CRUD operations, live price sync via yfinance, "
        "and advanced analytics (SMA, RSI). All public interfaces strictly "
        "use camelCase keys (e.g., assetId, lastPrice, marketCap) while the "
        "underlying database uses snake_case (PR #67 compliance)."
    ),
    lifespan=lifespan,
)


# ---------- EXCEPTION HANDLERS ----------
@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    logger.error(
        f"Business error [{exc.status_code}]: {exc.detail} "
        f"(path: {request.url.path}, resource key: asset_id)"
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException [{exc.status_code}]: {exc.detail} "
        f"(path: {request.url.path})"
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"Unhandled exception: {exc} (path: {request.url.path})", exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal error occurred."},
    )


# ---------- DEPENDENCIES ----------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# ---------- REST ENDPOINTS ----------
@app.get(
    "/status",
    response_model=Dict[str, str],
    summary="Healthcheck",
)
async def healthcheck():
    logger.info("Healthcheck requested.")
    return {"status": "ok", "database": "connected"}


@app.get(
    "/assets",
    response_model=List[FinancialAssetSchema],
    summary="List assets",
)
async def read_assets(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records (1-100)"),
    min_price: Optional[float] = Query(
        None, ge=0, description="Minimum lastPrice filter"
    ),
    sort_by: Optional[str] = Query(
        "ticker_symbol",
        description="Sort column (asset_id, ticker_symbol, current_market_price, market_cap, last_updated)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated, filtered, sorted assets in camelCase."""
    try:
        assets = await get_assets(
            skip=skip, limit=limit, min_price=min_price, sort_by=sort_by
        )
        logger.info(f"Fetched {len(assets)} assets.")
        return assets
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.get(
    "/assets/{ticker_symbol}",
    response_model=FinancialAssetSchema,
    summary="Get asset by ticker",
)
async def read_asset_by_ticker(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    asset = await get_asset_by_ticker(ticker_symbol)
    if asset is None:
        raise AssetNotFoundException(
            detail=f"Asset with ticker '{ticker_symbol}' not found (primary key: assetId)."
        )
    logger.info(f"Fetched asset: {asset.ticker_symbol} (assetId={asset.asset_id})")
    return asset


@app.post(
    "/assets",
    response_model=FinancialAssetSchema,
    status_code=201,
    summary="Create asset",
)
async def create_new_asset(
    asset_data: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Creates asset. Body must use camelCase (tickerSymbol, lastPrice, marketCap)."""
    try:
        new_asset = await create_asset(asset_data)
        logger.info(f"Created asset: {new_asset.asset_id} ({new_asset.ticker_symbol})")
        return new_asset
    except ValueError as e:
        logger.warning(f"Conflict creating asset: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating asset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.post(
    "/assets/sync",
    response_model=Dict[str, int],
    summary="Sync all prices",
)
async def sync_prices(
    db: AsyncSession = Depends(get_db),
):
    """Triggers a bulk update of lastPrice and lastUpdated from live market data."""
    try:
        result = await update_all_assets_prices(db)
        logger.info(f"Price sync completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Price sync failed: {e}")
        raise HTTPException(status_code=500, detail="Price synchronization error.")


@app.get(
    "/assets/{ticker_symbol}/analytics",
    response_model=AnalyticsResponse,
    summary="30‑day SMA & 14‑day RSI",
)
async def asset_analytics(
    ticker_symbol: str,
    db: AsyncSession = Depends(get_db),
):
    asset = await get_asset_by_ticker(ticker_symbol)
    if asset is None:
        raise AssetNotFoundException(
            detail=f"Asset with ticker '{ticker_symbol}' not found (primary key: assetId)."
        )
    try:
        prices = await get_historical_data(ticker_symbol, days=30)
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker_symbol}: {e}")
        raise HTTPException(status_code=502, detail="External data service error.")
    try:
        sma = calculate_moving_average(prices, window=30)
    except AnalyticsException as e:
        logger.warning(f"SMA calculation error for {ticker_symbol}: {e.detail}")
        raise
    try:
        rsi = calculate_rsi(prices, periods=14)
    except AnalyticsException as e:
        logger.warning(f"RSI calculation error for {ticker_symbol}: {e.detail}")
        raise

    logger.info(f"Analytics for {ticker_symbol}: SMA={sma}, RSI={rsi}")
    return AnalyticsResponse(
        ticker_symbol=ticker_symbol,
        moving_average_30d=sma,
        rsi_14=rsi,
    )


# ---------- COSMIC UI DASHBOARD ----------
@app.get("/dashboard", response_class=HTMLResponse, summary="Cosmic UI Dashboard")
async def dashboard():
    """Serves the premium dark‑themed SPA dashboard."""
    dashboard_path = Path(__file__).parent / "templates" / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard_path.read_text(encoding="utf-8")