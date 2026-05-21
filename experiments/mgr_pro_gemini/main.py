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
    """Lifecycle manager handling database initialization."""
    logger.info("Initializing database with snake_case schema.")
    
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        
        pragma_query = text("PRAGMA table_info(financial_assets);")
        result = await conn.execute(pragma_query)
        existing_columns = [row[1] for row in result.fetchall()]
        
        if "id" in existing_columns and "asset_id" not in existing_columns:
            logger.critical("Database validation failed. Forbidden 'id' column detected.")
            raise ValueError("Invalid Primary Key configuration. Must use 'asset_id'.")
            
    logger.info("Database validation successful. Ready to serve API requests in camelCase.")
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
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/status")
async def healthcheck():
    return {"status": "ok", "service": settings.APP_NAME}

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    minPrice: Optional[float] = Query(None, ge=0.0, alias="minPrice"),
    sortBy: str = Query("tickerSymbol", alias="sortBy"),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches a paginated list of assets. 
    Query parameters accept camelCase (minPrice, sortBy).
    """
    sort_mapping = {
        "assetId": "asset_id",
        "tickerSymbol": "ticker_symbol",
        "lastPrice": "last_price",
        "marketCap": "market_cap",
        "lastUpdated": "last_updated"
    }
    db_sort_by = sort_mapping.get(sortBy, "ticker_symbol")

    try:
        assets = await crud.get_assets(db, skip, limit, minPrice, db_sort_by)
    except Exception as e:
        logger.error(f"Database read failure: {e}")
        raise exceptions.DatabaseConnectionException()
        
    if not assets:
        raise exceptions.AssetNotFoundException(detail="No assets match the query parameters.")
    return assets

@app.get("/assets/{tickerSymbol}", response_model=schemas.FinancialAsset)
async def read_asset_by_ticker(tickerSymbol: str, db: AsyncSession = Depends(get_db)):
    """Retrieves specific details for a single asset."""
    asset = await crud.get_asset_by_ticker(db, tickerSymbol.upper())
    if not asset:
        raise exceptions.AssetNotFoundException()
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new asset.
    The payload MUST be provided in camelCase (e.g., tickerSymbol).
    Pydantic will automatically map it to the internal snake_case schema.
    """
    try:
        # The 'asset' object here already has internal attributes mapped as snake_case
        # (e.g., asset.ticker_symbol), so crud.create_asset requires zero modifications.
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
    try:
        results = await crud.update_all_assets_prices(db)
        return {"detail": f"Update processed successfully. Records updated: {results['updated']}", "failedTickers": results['failed']}
    except Exception as e:
        logger.error(f"Batch synchronization failed: {e}")
        raise exceptions.ExternalAPIException()

@app.get("/assets/{tickerSymbol}/analytics", response_model=schemas.AnalyticsResponse)
async def get_asset_analytics(tickerSymbol: str, db: AsyncSession = Depends(get_db)):
    ticker = tickerSymbol.upper()
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