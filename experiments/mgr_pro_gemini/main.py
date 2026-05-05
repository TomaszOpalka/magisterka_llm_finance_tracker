from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Local module imports
from database import AsyncSessionLocal, engine
import models
import crud
import schemas
import exceptions
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the FastAPI application lifecycle. 
    Ensures the 'financial_assets' table and its columns exist.
    """
    logger.info("Starting 'Finance Track' system. Verifying database structure.")
    
    async with engine.begin() as conn:
        # Step 1: Create tables if they do not exist
        await conn.run_sync(models.Base.metadata.create_all)
        
        # Step 2: Check columns asynchronously
        pragma_query = text("PRAGMA table_info(financial_assets);")
        result = await conn.execute(pragma_query)
        existing_columns = [row[1] for row in result.fetchall()]
        
        # Step 3: Manual migration if 'last_updated' is missing
        if "last_updated" not in existing_columns:
            logger.warning("Missing 'last_updated' column. Executing ALTER TABLE migration...")
            alter_query = text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME;")
            await conn.execute(alter_query)
            logger.info("Migration successful. 'last_updated' column added.")
            
    logger.info("Database is ready. Primary key 'asset_id' verified.")
    
    yield
    
    logger.info("Shutting down application. Disposing database engine.")
    await engine.dispose()


app = FastAPI(title="Finance Track API", lifespan=lifespan)


@app.exception_handler(exceptions.FinanceException)
async def finance_exception_handler(request: Request, exc: exceptions.FinanceException):
    """Handles core business logic exceptions."""
    logger.warning(f"Business Error [{exc.status_code}] at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(exceptions.ExternalAPIException)
async def external_api_exception_handler(request: Request, exc: exceptions.ExternalAPIException):
    """
    Catches specific external API errors globally, preventing the application
    from crashing and returning a clean 502 Bad Gateway response.
    """
    logger.error(f"External API Error at {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles standard HTTP exceptions gracefully."""
    logger.error(f"HTTP Exception {exc.status_code} at {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/status")
async def healthcheck():
    """Healthcheck endpoint to verify server status."""
    return {"status": "ok", "database": "connected"}


@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Optional[float] = Query(None, ge=0.0),
    sort_by: str = Query("ticker_symbol"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of assets with pagination, filtering, and sorting."""
    try:
        assets = await crud.get_assets(db=db, skip=skip, limit=limit, min_price=min_price, sort_by=sort_by)
    except Exception as e:
        logger.error(f"Query error in read_assets: {e}")
        raise exceptions.DatabaseConnectionException()
        
    if not assets:
        raise exceptions.AssetNotFoundException(detail="No financial assets found matching the criteria.")

    return assets


@app.get("/assets/{ticker_symbol}", response_model=schemas.FinancialAsset)
async def read_asset_by_ticker(
    ticker_symbol: str, 
    db: AsyncSession = Depends(get_db)
):
    """Fetches a single asset's details by its ticker symbol."""
    asset = await crud.get_asset_by_ticker(db, ticker_symbol=ticker_symbol.upper())
    if not asset:
        raise exceptions.AssetNotFoundException(detail=f"Asset with ticker '{ticker_symbol}' not found.")
    return asset


@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(
    asset: schemas.FinancialAssetCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Creates a new financial asset in the database."""
    try:
        created_asset = await crud.create_asset(db, asset)
        logger.info(f"Added new asset ({created_asset.ticker_symbol}). Asset ID: {created_asset.asset_id}")
        return created_asset
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ticker symbol already exists.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Critical save error: {e}")
        raise exceptions.DatabaseConnectionException()


@app.post("/assets/sync", status_code=200)
async def sync_asset_prices(db: AsyncSession = Depends(get_db)):
    """
    Triggers a mass update of all stock prices. Designed to be fault-tolerant.
    """
    try:
        logger.info("Starting mass price synchronization...")
        sync_results = await crud.update_all_assets_prices(db)
        
        logger.info(
            f"Synchronization complete. Updated: {sync_results['updated']}, "
            f"Failed: {len(sync_results['failed'])}"
        )
        
        return {
            "detail": f"Successfully synchronized {sync_results['updated']} assets.",
            "failed_tickers": sync_results['failed']
        }
    except Exception as e:
        logger.error(f"Critical error during synchronization batch: {e}")
        # Reraise as a custom exception to be caught by the global handler
        raise exceptions.ExternalAPIException(detail="Mass synchronization failed due to external provider issues.")