import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, AsyncGenerator

from fastapi import FastAPI, Depends, Query, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

import crud
import models
import schemas
import services
import analytics
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

# Standard initial seed set
INITIAL_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
    "TSLA", "META", "BTC-USD", "ETH-USD", "SPY"
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Self-healing lifespan context manager with automated data seeding.
    Verifies schema integrity, auto-patches SQLite column mismatches, 
    and populates default seed assets if the database is empty.
    """
    logger.info("Starting Finance Track API - Verifying Schema & Seed Registry.")
    await init_db()

    async with async_session() as session:
        async with session.begin():
            try:
                # 1. Schema self-healing for SQLite table columns
                result = await session.execute(text("PRAGMA table_info(financial_assets)"))
                columns = [row[1] for row in result.fetchall()]

                if columns:
                    if "current_market_price" not in columns:
                        if "last_price" in columns:
                            logger.info("Migrating schema: RENAME 'last_price' -> 'current_market_price'")
                            await session.execute(text("ALTER TABLE financial_assets RENAME COLUMN last_price TO current_market_price"))
                        else:
                            logger.info("Migrating schema: ADD 'current_market_price'")
                            await session.execute(text("ALTER TABLE financial_assets ADD COLUMN current_market_price FLOAT DEFAULT 0.0 NOT NULL"))

                    if "last_updated" not in columns:
                        logger.info("Migrating schema: ADD 'last_updated'")
                        await session.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))

                # 2. Automated Initial Data Seeding
                count_query = await session.execute(select(func.count()).select_from(models.FinancialAsset))
                asset_count = count_query.scalar() or 0

                if asset_count == 0:
                    logger.info("Database empty on cold-start. Seeding 10 default financial assets.")
                    for ticker in INITIAL_TICKERS:
                        seeded_asset = models.FinancialAsset(
                            asset_id=str(uuid.uuid4()),
                            ticker_symbol=ticker,
                            current_market_price=0.0,
                            market_cap=0.0,
                            last_updated=datetime.utcnow()
                        )
                        session.add(seeded_asset)
                    logger.info("Default ticker seed sequence complete.")
            except Exception as e:
                logger.error(f"Startup execution error: {str(e)}")

    yield
    logger.info("Shutting down Finance Track API services.")


app = FastAPI(
    title="Finance Track API",
    version="1.0.0",
    description="Asynchronous financial telemetry engine built with FastAPI, SQLAlchemy 2.0, and Pydantic v2. Exposes strict camelCase schemas to presentation layers while maintaining decoupled internal snake_case database persistence.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    logger.warning(f"Domain Exception: {exc.message} at {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "errorType": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."}
    )

# --- Dependency Injection ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Endpoints & SPA Router ---

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def render_dashboard():
    """Serves the Cosmic UI Single Page Application."""
    dashboard_path = os.path.join("templates", "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1 style='color:red;'>Dashboard template missing. Ensure templates/dashboard.html exists.</h1>",
        status_code=404
    )

@app.get("/status", tags=["System"])
async def get_status():
    return {
        "status": "active",
        "databaseProvider": "SQLite (aiosqlite)",
        "apiVersion": "1.0.0",
        "primaryKeyContract": "assetId"
    }

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_assets(db, skip=skip, limit=limit)

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not asset:
        raise AssetNotFoundException(f"Asset '{ticker_symbol}' not found.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse, tags=["Analytics"])
async def get_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    db_asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not db_asset:
        raise AssetNotFoundException(f"Analytics engine aborted: {ticker_symbol} does not exist.")

    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if len(history) < 15:
        raise FinanceException(f"Insufficient historical data points to compute analytics for {ticker_symbol}.")

    sma = analytics.calculate_moving_average(history)
    rsi = analytics.calculate_rsi(history, periods=14)

    return schemas.AnalyticsResponse(
        ticker_symbol=ticker_symbol.upper(),
        moving_average_30d=sma,
        rsi_14=rsi,
        data_points=len(history)
    )

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def create_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Accepts JSON containing {"tickerSymbol": "..."}.
    Automatically maps camelCase attributes into database models.
    """
    existing = await crud.get_asset_by_ticker(db, asset.ticker_symbol.upper())
    if existing:
        raise FinanceException(f"Asset '{asset.ticker_symbol.upper()}' is already registered.", status_code=400)
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Asset registration error: {str(e)}")
        raise FinanceException("Integrity error processing request payload. Verify constraints.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_assets(db: AsyncSession = Depends(get_db)):
    """
    Triggers market data synchronization for all registered assets.
    Returns HTTP 502 Bad Gateway on upstream provider failures.
    """
    try:
        updated_count = await crud.update_all_assets_prices(db)
        return {
            "status": "success",
            "updatedRecords": updated_count
        }
    except Exception as e:
        logger.error(f"Upstream provider failure during sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External market data provider unreachable or timed out. Sync aborted."
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)