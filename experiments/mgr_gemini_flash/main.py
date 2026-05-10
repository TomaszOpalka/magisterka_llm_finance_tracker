import crud
import schemas
import services
import analytics
import models
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
    Manages the application lifecycle.
    Initializes the database and performs schema migrations for asset_id and last_updated.
    """
    logger.info("--- Finance Track System: Starting Up ---")
    
    # 1. Initialize tables
    await init_db()
    
    # 2. Resilient migration for SQLite
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Migration: Adding 'last_updated' column to 'financial_assets'.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
                logger.info("Migration successful.")
            else:
                logger.info("Database verification: Schema is current (Contract: asset_id).")
        except Exception as e:
            logger.error(f"Startup maintenance error: {str(e)}")

    yield
    logger.info("--- Finance Track System: Shutting Down ---")

# --- App Initialization ---

app = FastAPI(
    title="Finance Track API",
    version="3.3.1",
    description="Asynchronous Financial Tracker with SMA and RSI Analytics.",
    lifespan=lifespan
)

# --- CORS Configuration ---

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
    """Handles custom business exceptions and logs warnings."""
    logger.warning(f"Business Exception: {exc.message} | URL: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_type": exc.__class__.__name__,
            "detail": exc.message,
            "path": str(request.url.path),
            "pk_contract": "asset_id"
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global safety net for unhandled internal server errors."""
    logger.error(f"Critical System Error: {str(exc)} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Verify logs in data/finance.log."}
    )

# --- Dependency Injection ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a scoped asynchronous database session per request."""
    async with async_session() as session:
        yield session

# --- API Endpoints ---

@app.get("/status", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "online",
        "database": "connected",
        "pk_convention": "asset_id",
        "port_mapping": "8002:8002"
    }

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query(
        "ticker_symbol", 
        pattern="^(ticker_symbol|last_price|market_cap|asset_id)$"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all assets from the database with pagination and sorting."""
    return await crud.get_assets(db, skip, limit, min_price, sort_by)

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Fetches details for a single asset from the local DB."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol)
    if not asset:
        raise AssetNotFoundException(f"Asset '{ticker_symbol}' not found in registry.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", response_model=schemas.AnalyticsResponse, tags=["Analytics"])
async def get_asset_analytics(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Performs advanced technical analysis (SMA and RSI).
    Requires the asset to be registered in the DB first (Data Hardening).
    """
    # 1. Verify asset existence in local DB
    db_asset = await crud.get_asset_by_ticker(db, ticker_symbol.upper())
    if not db_asset:
        raise AssetNotFoundException(
            f"Asset {ticker_symbol} must be added to the database via POST /assets "
            f"before running analytics."
        )

    # 2. Fetch historical market data (30 days)
    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if len(history) < 15:
        raise FinanceException(f"Insufficient history (need 15+ points) for {ticker_symbol}.")

    # 3. Calculate indicators
    sma = analytics.calculate_moving_average(history)
    rsi = analytics.calculate_rsi(history, periods=14)

    return schemas.AnalyticsResponse(
        ticker_symbol=ticker_symbol.upper(),
        moving_average_30d=sma,
        rsi_14=rsi,
        data_points=len(history)
    )

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new asset. Ticker symbols are normalized to uppercase."""
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Failure to create asset: {str(e)}")
        raise FinanceException("Integrity error: Duplicate ticker or database constraint.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_market_data(db: AsyncSession = Depends(get_db)):
    """Mass-syncs current prices for all stored assets."""
    logger.info("Executing global asset synchronization...")
    try:
        updated_count = await crud.update_all_assets_prices(db)
        return {
            "status": "success",
            "updated_records": updated_count,
            "pk_contract": "asset_id_preserved"
        }
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise FinanceException("Internal sync process failed.", status_code=500)

if __name__ == "__main__":
    import uvicorn
    # Enforcing port 8002 to align with Docker mapping 8002:8002
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)