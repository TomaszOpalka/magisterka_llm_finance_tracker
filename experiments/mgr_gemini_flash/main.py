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
    Handles application startup and shutdown.
    Initializes the database and ensures schema synchronization 
    while preserving snake_case naming in the database layer.
    """
    logger.info("Initializing Finance Track Services - CamelCase API Layer Active")
    await init_db()
    
    async with engine.begin() as conn:
        try:
            # Check for existing columns to maintain SQLite compatibility
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Database Migration: Adding last_updated column.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
            
            logger.info("Database connection established. Primary Key: asset_id")
        except Exception as e:
            logger.error(f"Startup schema synchronization failed: {str(e)}")

    yield
    logger.info("Finance Track API services are shutting down.")

app = FastAPI(
    title="Finance Track API",
    version="4.0.0",
    description="Refactored API using camelCase for JSON and snake_case for Database.",
    lifespan=lifespan
)

# CORS Configuration for research and frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handlers ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """Returns business logic errors using camelCase keys in the response."""
    logger.warning(f"Business Exception: {exc.message} at {request.url.path}")
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
    """Catch-all for unhandled server errors."""
    logger.error(f"Critical System Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred. Check logs for details."}
    )

# --- Dependency Injection ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Scoped asynchronous database session generator."""
    async with async_session() as session:
        yield session

# --- API Endpoints ---

@app.get("/status", tags=["System"])
async def get_status():
    """Simple health check returning camelCase keys."""
    return {
        "status": "online",
        "apiVersion": "4.0.0",
        "primaryKeyContract": "assetId"
    }

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves assets from the snake_case database and 
    automatically transforms them to camelCase for the response.
    """
    assets = await crud.get_assets(db, skip=skip, limit=limit)
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Fetches a specific asset by its ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not asset:
        raise AssetNotFoundException(f"Asset {ticker_symbol} not found in the research database.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse, tags=["Analytics"])
async def get_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Returns advanced analytics.
    Verification is done using snake_case internal logic, 
    but response is mapped to camelCase.
    """
    db_asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not db_asset:
        raise AssetNotFoundException(f"Analytics failed: {ticker_symbol} is not registered.")

    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if len(history) < 15:
        raise FinanceException(f"Insufficient history to generate RSI and SMA for {ticker_symbol}.")

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
    Accepts camelCase JSON (e.g., tickerSymbol) and 
    maps it to the snake_case database model via the CRUD layer.
    """
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Asset creation error: {str(e)}")
        raise FinanceException("Integrity error. Ensure tickerSymbol is unique.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_assets(db: AsyncSession = Depends(get_db)):
    """Triggers a mass-update of prices. Returns success in camelCase."""
    updated_count = await crud.update_all_assets_prices(db)
    return {
        "status": "success",
        "updatedRecords": updated_count
    }

if __name__ == "__main__":
    import uvicorn
    # Listening on 0.0.0.0 and port 8002 to match the Docker container mapping.
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)