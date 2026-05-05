from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

import crud
import schemas
import services
import analytics
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown.
    Ensures the database schema (including asset_id PK) is initialized and updated.
    """
    logger.info("--- Finance Track System: Initializing ---")
    await init_db()
    
    # Auto-migration logic for SQLite
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            if "last_updated" not in columns:
                logger.info("Migration: Adding 'last_updated' column.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")

    yield
    logger.info("--- Finance Track System: Shutting Down ---")

app = FastAPI(
    title="Finance Track API",
    version="3.2.0",
    lifespan=lifespan
)

# --- Exception Handlers ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    logger.warning(f"Business error: {exc.message} at {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.message}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Critical System Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

# --- Dependency ---

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Endpoints ---

@app.get("/status")
async def health_check():
    return {"status": "online", "pk_contract": "asset_id"}

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("ticker_symbol", pattern="^(ticker_symbol|last_price|market_cap|asset_id)$"),
    db: AsyncSession = Depends(get_db)
):
    assets = await crud.get_assets(db, skip, limit, min_price, sort_by)
    if not assets and skip == 0:
        raise AssetNotFoundException("No assets registered in the system.")
    return assets

@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset(ticker_symbol: str, db: AsyncSession = Depends(get_db)):
    asset = await crud.get_asset_by_ticker(db, ticker_symbol)
    if not asset:
        raise AssetNotFoundException(f"Ticker {ticker_symbol} not found in database.")
    return asset

@app.get("/assets/{ticker_symbol}/analytics", tags=["Analytics"])
async def get_asset_analytics(ticker_symbol: str):
    """
    Calculates moving average based on live historical data.
    Does not require the asset to be pre-registered in the DB.
    """
    history = await services.get_historical_data(ticker_symbol.upper(), days=30)
    if not history:
        raise AssetNotFoundException(f"Could not retrieve history for {ticker_symbol}")

    sma = analytics.calculate_moving_average(history)
    return {
        "ticker_symbol": ticker_symbol.upper(),
        "moving_average_30d": sma,
        "data_points": len(history)
    }

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.create_asset(db, asset)
    except Exception:
        raise FinanceException("Asset creation failed. Ensure ticker is unique.")

@app.post("/assets/sync", tags=["Maintenance"])
async def sync_prices(db: AsyncSession = Depends(get_db)):
    updated = await crud.update_all_assets_prices(db)
    return {"status": "success", "updated_count": updated}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)