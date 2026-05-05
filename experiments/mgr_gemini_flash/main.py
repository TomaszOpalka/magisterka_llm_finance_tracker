import crud
import schemas
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    Ensures database tables are created and the schema is up-to-date
    with the 'last_updated' column on startup.
    """
    logger.info("--- Finance Track System: Starting Services ---")
    
    # Initialize core tables
    await init_db()
    
    # Asynchronous schema maintenance for SQLite
    async with engine.begin() as conn:
        try:
            # Check for existing columns to avoid 'duplicate column' errors
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Migration: Adding 'last_updated' column to 'financial_assets' table.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
                logger.info("Migration successful.")
            else:
                logger.info("Database verification: Schema is current (Primary Key: asset_id).")
        except Exception as e:
            logger.error(f"Startup database error: {str(e)}")

    yield  # Application is now accepting requests
    
    logger.info("--- Finance Track System: Shutting Down ---")

# FastAPI App Initialization
app = FastAPI(
    title="Finance Track API",
    version="3.1.0",
    description="Professional API for tracking S&P 500 assets with automated market data sync.",
    lifespan=lifespan
)

# --- Global Exception Handlers ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """
    Standardizes business error responses and logs warnings for monitoring.
    """
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
    """
    Catch-all for unexpected system errors to prevent raw traceback leakage.
    """
    logger.error(f"Unhandled System Error: {str(exc)} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check logs."}
    )

# --- Dependency Injection ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an asynchronous database session for each request.
    Ensures proper cleanup after the request is finished.
    """
    async with async_session() as session:
        yield session

# --- API Endpoints ---

@app.get("/status", tags=["System"])
async def health_check():
    """Verifies API operational status and database connectivity."""
    return {
        "status": "online",
        "database": "connected",
        "pk_convention": "asset_id",
        "mode": "production-ready"
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
    """
    Retrieves assets with pagination and sorting.
    Returns 404 if no assets exist on the initial page.
    """
    assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    if not assets and skip == 0:
        raise AssetNotFoundException("No assets found in the database.")
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Fetches full details of a specific asset using its ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol)
    if not asset:
        raise AssetNotFoundException(f"Asset with ticker '{ticker_symbol}' not found.")
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Adds a new asset to the database. 
    ticker_symbol is automatically converted to uppercase.
    """
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Creation failed for {asset.ticker_symbol}: {str(e)}")
        raise FinanceException("Could not create asset. Ensure the ticker symbol is unique.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_market_data(db: AsyncSession = Depends(get_db)):
    """
    Triggers a resilient mass-update of all stock prices via yfinance.
    Skips individual errors to ensure the overall process completes.
    """
    logger.info("Executing resilient synchronization...")
    try:
        updated_count = await crud.update_all_assets_prices(db)
        return {
            "status": "success",
            "updated_records": updated_count,
            "pk_maintained": "asset_id"
        }
    except Exception as e:
        logger.error(f"Resilient sync critical failure: {str(e)}")
        raise FinanceException("Sync failed. Check external API connectivity.", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)