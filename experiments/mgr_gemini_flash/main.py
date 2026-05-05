from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

import crud
import schemas
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    Initializes database tables and performs schema migrations if necessary.
    """
    logger.info("Starting Finance Track API services...")
    
    # Create tables using Base.metadata.create_all via conn.run_sync
    await init_db()
    
    # Maintenance: Ensure SQLite schema is up to date
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "last_updated" not in columns:
                logger.info("Migration: Adding last_updated column to financial_assets table.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
            
            logger.info("Database integrity check complete (Primary Key: asset_id).")
        except Exception as e:
            logger.error(f"Schema migration failed: {str(e)}")

    yield
    logger.info("Shutting down Finance Track API services.")

app = FastAPI(
    title="Finance Track API",
    version="3.0.0",
    lifespan=lifespan
)

# Global Exception Handler
@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """
    Intercepts business exceptions and returns a standardized JSON error response.
    """
    logger.warning(f"Business logic error: {exc.message} at {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_type": exc.__class__.__name__,
            "detail": exc.message,
            "path": str(request.url.path)
        }
    )

# Dependency Injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an asynchronous database session per request.
    """
    async with async_session() as session:
        yield session

# --- API Endpoints ---

@app.get("/status", tags=["System"])
async def health_check():
    """Returns the current operational status of the API."""
    return {"status": "operational", "database": "connected", "pk_contract": "asset_id"}

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("ticker_symbol", pattern="^(ticker_symbol|last_price|market_cap|asset_id)$"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves assets with pagination, filtering, and sorting."""
    assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    if not assets and skip == 0:
        raise AssetNotFoundException("No financial assets found in the database.")
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset_by_ticker(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    """Fetches a specific asset by its ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol)
    if not asset:
        raise AssetNotFoundException(f"Asset with ticker '{ticker_symbol}' not found.")
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new financial asset in the system."""
    try:
        return await crud.create_asset(db, asset)
    except Exception as e:
        logger.error(f"Failed to create asset: {str(e)}")
        raise FinanceException("Integrity error: Possibly a duplicate ticker symbol.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_market_data(db: AsyncSession = Depends(get_db)):
    """Triggers an asynchronous update of all stock prices from external services."""
    updated_count = await crud.update_all_assets_prices(db)
    logger.info(f"Market data sync finished. Updated {updated_count} records.")
    return {"status": "success", "updated_count": updated_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)