import logging
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List, Optional, AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Local module imports
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
    """
    Lifecycle manager handling database initialization, self-healing schema validation,
    and automated data seeding for fresh installations.
    """
    logger.info("Initializing database with schema validation and self-healing protocols.")
    
    async with engine.begin() as conn:
        # Step 1: Safely create all tables if they don't exist
        await conn.run_sync(models.Base.metadata.create_all)
        
        # Step 2: Extract current schema from SQLite
        pragma_query = text("PRAGMA table_info(financial_assets);")
        result = await conn.execute(pragma_query)
        existing_columns = [row[1] for row in result.fetchall()]
        
        # Step 3: Self-Healing - Column Mutations
        if "id" in existing_columns and "asset_id" not in existing_columns:
            logger.critical("Database validation failed. Forbidden 'id' column detected.")
            raise ValueError("Invalid Primary Key configuration. Must use 'asset_id'.")
            
        if "last_updated" not in existing_columns:
            logger.info("Executing migration: Adding 'last_updated' column.")
            await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME;"))
            
        if "last_price" in existing_columns and "current_market_price" not in existing_columns:
            logger.warning("Executing migration: Renaming 'last_price' to 'current_market_price'.")
            await conn.execute(text("ALTER TABLE financial_assets RENAME COLUMN last_price TO current_market_price;"))

        # Step 4: Automatic Data Seeding for Fresh Installations
        count_query = text("SELECT COUNT(*) FROM financial_assets;")
        count = (await conn.execute(count_query)).scalar()
        
        if count == 0:
            logger.info("Empty database detected. Seeding 10 default financial assets...")
            default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BTC-USD", "ETH-USD", "SPY"]
            
            for ticker in default_tickers:
                insert_query = text("""
                    INSERT INTO financial_assets (asset_id, ticker_symbol, current_market_price, market_cap, last_updated) 
                    VALUES (:id, :ticker, 0.0, 0.0, :now)
                """)
                await conn.execute(insert_query, {
                    "id": str(uuid.uuid4()), 
                    "ticker": ticker, 
                    "now": datetime.now(timezone.utc)
                })
            logger.info("Database successfully seeded with default assets.")
            
    logger.info("Database validation successful. API is ready.")
    yield
    await engine.dispose()
    logger.info("Database connections terminated cleanly.")


api_description = """
### High-Performance Asynchronous Financial Tracking API
Welcome to the core backend of **Finance Track**.

#### Architecture Highlights:
* **Fully Asynchronous:** Utilizes `asyncio`, `httpx`, and `aiosqlite` for non-blocking I/O.
* **PR #67 Compliance:** Strict separation of internal database layout (snake_case) and public API contract (camelCase).
* **Data Hardening:** Pydantic v2 schemas rigorously validate inbound and outbound payloads.
* **Cosmic UI Integration:** Embedded SPA dashboard for real-time market monitoring.
"""

app = FastAPI(
    title="Finance Track API",
    version="1.0.0",
    description=api_description,
    lifespan=lifespan,
    contact={
        "name": "Finance Track Engineering",
        "email": "engineering@financetrack.local",
    }
)

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


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def render_dashboard():
    """Serves the Cosmic UI Single Page Application."""
    template_path = Path("templates/dashboard.html")
    if not template_path.exists():
        # Graceful fallback if the template directory is missing
        return HTMLResponse(
            "<h1>System Error: Dashboard template not found.</h1><p>Ensure templates/dashboard.html exists.</p>", 
            status_code=404
        )
    
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/status", tags=["System"])
async def healthcheck():
    return {"status": "ok", "service": "Finance Track"}

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    minPrice: Optional[float] = Query(None, ge=0.0, alias="minPrice"),
    sortBy: str = Query("tickerSymbol", alias="sortBy"),
    db: AsyncSession = Depends(get_db)
):
    """Fetches a paginated list of assets. Returns camelCase JSON mapping via Pydantic."""
    sort_mapping = {
        "assetId": "asset_id",
        "tickerSymbol": "ticker_symbol",
        "currentMarketPrice": "current_market_price",
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

@app.get("/assets/{tickerSymbol}", response_model=schemas.FinancialAsset, tags=["Assets"])
async def read_asset_by_ticker(tickerSymbol: str, db: AsyncSession = Depends(get_db)):
    asset = await crud.get_asset_by_ticker(db, tickerSymbol.upper())
    if not asset:
        raise exceptions.AssetNotFoundException()
    return asset

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.create_asset(db, asset)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ticker symbol must be unique.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Database write failure: {e}")
        raise exceptions.DatabaseConnectionException()

@app.post("/assets/sync", status_code=200, tags=["Operations"])
async def sync_asset_prices(db: AsyncSession = Depends(get_db)):
    """
    Triggers a mass update of all tracked asset prices.
    Safely handles provider failures by returning an HTTP 502 Bad Gateway.
    """
    try:
        results = await crud.update_all_assets_prices(db)
        return {
            "detail": f"Update processed successfully. Records updated: {results['updated']}", 
            "failedTickers": results['failed']
        }
    except Exception as e:
        logger.error(f"Batch synchronization failed during external call: {e}")
        # Explicit 502 Bad Gateway response prevents backend crashes and informs the client correctly
        raise HTTPException(
            status_code=502, 
            detail="Bad Gateway: External synchronization provider failed or timed out."
        )

@app.get("/assets/{tickerSymbol}/analytics", response_model=schemas.AnalyticsResponse, tags=["Analytics"])
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