import logging
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from config import settings
from database import AsyncSessionLocal, engine
import models
import crud
import schemas
import exceptions
import services
import analytics

logger = logging.getLogger("finance_track")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager handling database schema initialization and validation."""
    logger.info("Initializing database and verifying architecture constraints.")
    
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        
        pragma_query = text("PRAGMA table_info(financial_assets);")
        result = await conn.execute(pragma_query)
        existing_columns = [row[1] for row in result.fetchall()]
        
        if "last_updated" not in existing_columns:
            logger.info("Executing migration: Adding 'last_updated' column.")
            await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME;"))
            
        if "id" in existing_columns and "asset_id" not in existing_columns:
            logger.critical("Database validation failed. Forbidden 'id' column detected.")
            raise ValueError("Invalid Primary Key configuration. Must use 'asset_id'.")
            
    logger.info("Database validation successful. 'asset_id' confirmed as Primary Key.")
    yield
    await engine.dispose()
    logger.info("Database connections terminated cleanly.")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


@app.exception_handler(exceptions.FinanceException)
async def finance_exception_handler(request: Request, exc: exceptions.FinanceException):
    logger.warning(f"Business logic rule triggered at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(exceptions.ExternalAPIException)
async def external_api_exception_handler(request: Request, exc: exceptions.ExternalAPIException):
    logger.error(f"External provider failure at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/status")
async def healthcheck():
    """Validates the API operational status."""
    return {"status": "ok", "service": settings.APP_NAME}

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0.0),
    sort_by: str = Query("ticker_symbol"),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a paginated and sorted list of tracked assets."""
    try:
        assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    except Exception as e:
        logger.error(f"Database read failure: {e}")
        raise exceptions.DatabaseConnectionException()
        
    if not assets:
        raise exceptions.AssetNotFoundException(detail="No assets match the query parameters.")
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset)
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Retrieves specific details for a single asset."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not asset:
        raise exceptions.AssetNotFoundException()
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new asset into the tracking system."""
    try:
        return await crud.create_asset(db, asset)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ticker symbol must be unique.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Database write failure: {e}")
        raise exceptions.DatabaseConnectionException()

@app.post("/assets/sync", status_code=200)
async def sync_asset_prices(db: AsyncSession = Depends(get_db)):
    """Initiates a batch update of current market prices."""
    try:
        results = await crud.update_all_assets_prices(db)
        return {"detail": f"Update processed successfully. Records updated: {results['updated']}", "failed": results['failed']}
    except Exception as e:
        logger.error(f"Batch synchronization failed: {e}")
        raise exceptions.ExternalAPIException()

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse)
async def get_asset_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Computes technical indicators for a specific asset using historical data."""
    ticker = ticker_symbol.upper()
    asset = await crud.get_asset_by_ticker(db, ticker)
    
    if not asset:
        raise exceptions.AssetNotFoundException()
        
    prices = await services.get_historical_data(ticker, days=60)
    sma = analytics.calculate_moving_average(prices, period=30)
    rsi = analytics.calculate_rsi(prices, periods=14)
    
    if sma is None and rsi is None:
        raise HTTPException(status_code=422, detail="Market data insufficient for technical analysis.")
        
    return schemas.AnalyticsResponse(
        ticker_symbol=ticker, 
        moving_average_30d=sma, 
        rsi_14=rsi
    )