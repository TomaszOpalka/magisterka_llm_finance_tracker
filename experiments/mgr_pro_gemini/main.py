import logging
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Local module imports
from config import settings
from database import AsyncSessionLocal, engine
import models
import crud
import schemas
import exceptions
import services
import analytics

# Logging configuration
logger = logging.getLogger("finance_track")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the FastAPI application lifecycle. 
    Handles database initialization and manual schema migrations.
    """
    logger.info(f"Starting '{settings.APP_NAME}'. Database initialization in progress.")
    
    async with engine.begin() as conn:
        # Step 1: Ensure tables exist
        await conn.run_sync(models.Base.metadata.create_all)
        
        # Step 2: Check for existing columns to handle migrations
        pragma_query = text("PRAGMA table_info(financial_assets);")
        result = await conn.execute(pragma_query)
        existing_columns = [row[1] for row in result.fetchall()]
        
        # Step 3: Migration - Add last_updated if it's a legacy database
        if "last_updated" not in existing_columns:
            logger.warning("Migration: Adding missing 'last_updated' column.")
            await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME;"))
            
        # Step 4: Strict Architecture Check (No 'id', only 'asset_id')
        if "id" in existing_columns and "asset_id" not in existing_columns:
            logger.critical("Architecture violation: 'id' found. System requires 'asset_id'.")
            raise Exception("Database Primary Key Mismatch.")
            
    logger.info("Database migration and verification complete.")
    yield
    await engine.dispose()
    logger.info("Application shutdown: Database engine disposed.")

# Application instance
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# --- GLOBAL EXCEPTION HANDLERS ---

@app.exception_handler(exceptions.FinanceException)
async def finance_exception_handler(request: Request, exc: exceptions.FinanceException):
    logger.warning(f"Business Logic Error [{exc.status_code}] at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(exceptions.ExternalAPIException)
async def external_api_exception_handler(request: Request, exc: exceptions.ExternalAPIException):
    logger.error(f"External Provider Error at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- DEPENDENCIES ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# --- ENDPOINTS ---

@app.get("/status")
async def healthcheck():
    """Service availability check."""
    return {"status": "ok", "database": "connected", "app": settings.APP_NAME}

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0.0),
    sort_by: str = Query("ticker_symbol"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves assets with pagination, filtering by price, and custom sorting."""
    try:
        assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    except Exception as e:
        logger.error(f"Database Query Error: {e}")
        raise exceptions.DatabaseConnectionException()
        
    if not assets:
        raise exceptions.AssetNotFoundException()
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset)
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Finds a specific asset by ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not asset:
        raise exceptions.AssetNotFoundException(detail=f"Ticker {ticker_symbol} not found.")
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new asset. Enforces unique ticker symbols."""
    try:
        return await crud.create_asset(db, asset)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ticker symbol already exists.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Persistence Error: {e}")
        raise exceptions.DatabaseConnectionException()

@app.post("/assets/sync", status_code=200)
async def sync_asset_prices(db: AsyncSession = Depends(get_db)):
    """Triggers mass price synchronization with fault tolerance for individual tickers."""
    try:
        results = await crud.update_all_assets_prices(db)
        return {"detail": f"Synced {results['updated']} assets.", "failed": results['failed']}
    except Exception as e:
        logger.error(f"Mass Sync Failed: {e}")
        raise exceptions.ExternalAPIException()

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse)
async def get_asset_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Performs technical analysis (SMA, RSI) for a registered asset."""
    ticker = ticker_symbol.upper()
    asset = await crud.get_asset_by_ticker(db, ticker)
    
    if not asset:
        raise exceptions.AssetNotFoundException()
        
    prices = await services.get_historical_data(ticker, days=60)
    sma = analytics.calculate_moving_average(prices, 30)
    rsi = analytics.calculate_rsi(prices, 14)
    
    if sma is None and rsi is None:
        raise HTTPException(status_code=422, detail="Insufficient market data for analytics.")
        
    return schemas.AnalyticsResponse(ticker_symbol=ticker, moving_average_30d=sma, rsi_14=rsi)