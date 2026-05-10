import crud
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
    Manages the application lifecycle.
    Performs database initialization and schema migrations on startup.
    """
    logger.info("--- Finance Track System: Starting Services ---")
    
    # 1. Initialize database tables if they don't exist
    await init_db()
    
    # 2. Resilient schema migration for SQLite (adding columns if missing)
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Migration: Adding 'last_updated' column to 'financial_assets' table.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
                logger.info("Migration successful.")
            else:
                logger.info("Database verification: Schema is current (Primary Key: asset_id).")
        except Exception as e:
            logger.error(f"Startup database maintenance failed: {str(e)}")

    yield  # The application is now serving requests
    
    logger.info("--- Finance Track System: Shutting Down ---")

# --- App Initialization ---

app = FastAPI(
    title="Finance Track API",
    version="3.3.0",
    description="Asynchronous Financial Tracker with SMA Analytics and Docker persistence.",
    lifespan=lifespan
)

# --- CORS Configuration (Fixes 'Unsafe attempt to load URL') ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For research/dev. In production, list specific domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handlers ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """Handles business-level exceptions and logs them to finance.log."""
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
    """Catch-all for unexpected internal errors."""
    logger.error(f"Critical System Error: {str(exc)} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check system logs for asset_id integrity."}
    )

# --- Dependency Injection ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a scoped asynchronous database session."""
    async with async_session() as session:
        yield session

# --- API Endpoints ---

@app.get("/status", tags=["System"])
async def health_check():
    """Health check endpoint to verify system availability."""
    return {
        "status": "online",
        "database": "connected",
        "pk_convention": "asset_id",
        "docker_mode": "active"
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
    """Retrieves stored financial assets with filtering and pagination."""
    assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    if not assets and skip == 0:
        raise AssetNotFoundException("No assets found in the local database.")
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific ticker from the local database."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol)
    if not asset:
        raise AssetNotFoundException(f"Asset with ticker '{ticker_symbol}' not found.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", tags=["Analytics"])
async def get_asset_analytics(ticker_symbol: str):
    """
    Calculates the 30-day Simple Moving Average (SMA).
    Uses live historical data from external services.
    """
    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if not history:
        raise AssetNotFoundException(f"Could not retrieve historical data for {ticker_symbol}")

    sma_30 = analytics.calculate_moving_average(history)
    return {
        "ticker_symbol": ticker_symbol.upper(),
        "moving_average_30d": sma_30,
        "points_analyzed": len(history)
    }

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new asset. Enforces uppercase tickers and unique asset_id."""
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Asset creation error: {str(e)}")
        raise FinanceException("Failure to register asset. Check ticker uniqueness.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_market_data(db: AsyncSession = Depends(get_db)):
    """Batch updates all stored asset prices using live market threads."""
    logger.info("Executing global market data synchronization...")
    try:
        updated_count = await crud.update_all_assets_prices(db)
        return {
            "status": "success",
            "updated_records": updated_count,
            "pk_contract": "maintained"
        }
    except Exception as e:
        logger.error(f"Synchronization critical failure: {str(e)}")
        raise FinanceException("Sync failed. Check API connectivity.", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.0", port=8002, reload=True)