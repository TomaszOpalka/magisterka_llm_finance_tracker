import crud
import models
import schemas
import services
import analytics
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    Initializes the database and ensures the schema is synchronized.
    """
    logger.info("Starting Finance Track API services.")
    await init_db()
    
    async with engine.begin() as conn:
        try:
            # Verify existing columns for SQLite compatibility
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Schema Update: Adding last_updated column.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
            
            logger.info("Database schema verification successful (PK: asset_id).")
        except Exception as e:
            logger.error(f"Schema synchronization failed: {str(e)}")

    yield
    logger.info("Shutting down Finance Track API services.")

app = FastAPI(
    title="Finance Track API",
    version="3.4.0",
    lifespan=lifespan
)

# CORS Configuration for cross-origin research tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.message}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

# Dependency Injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# API Endpoints
@app.get("/status", tags=["System"])
async def get_status():
    """Returns the operational status of the API."""
    return {"status": "online", "pk_contract": "asset_id"}

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of financial assets from the local database."""
    assets = await crud.get_assets(db, skip=skip, limit=limit)
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a specific asset by its ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not asset:
        raise AssetNotFoundException(f"Asset {ticker_symbol} not found.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse, tags=["Analytics"])
async def get_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Calculates technical indicators for a registered asset.
    Requires the asset to exist in the database for research integrity.
    """
    db_asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not db_asset:
        raise AssetNotFoundException(f"Analytics failed: {ticker_symbol} is not registered.")

    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if len(history) < 15:
        raise FinanceException("Insufficient historical data for RSI calculation.")

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
    """Registers a new financial asset with a unique asset_id."""
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Asset registration error: {str(e)}")
        raise FinanceException("Could not create asset. Ensure ticker uniqueness.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_assets(db: AsyncSession = Depends(get_db)):
    """Synchronizes local prices with live market data."""
    updated = await crud.update_all_assets_prices(db)
    return {"status": "success", "updated_count": updated}