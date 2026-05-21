import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
import logging

import models
import schemas
import services

logger = logging.getLogger("finance_track")

async def get_assets(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    min_price: float | None = None, 
    sort_by: str = "ticker_symbol"
) -> List[models.FinancialAsset]:
    """Retrieves assets utilizing the newly refactored current_market_price column."""
    query = select(models.FinancialAsset)
    
    if min_price is not None:
        query = query.where(models.FinancialAsset.current_market_price >= min_price)
        
    sort_options = {
        "asset_id": models.FinancialAsset.asset_id,
        "ticker_symbol": models.FinancialAsset.ticker_symbol,
        "current_market_price": models.FinancialAsset.current_market_price,
        "market_cap": models.FinancialAsset.market_cap,
        "last_updated": models.FinancialAsset.last_updated
    }
    
    sort_column = sort_options.get(sort_by, models.FinancialAsset.ticker_symbol)
    query = query.order_by(sort_column).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_asset_by_ticker(db: AsyncSession, ticker_symbol: str) -> models.FinancialAsset | None:
    """Retrieves a single asset by its unique ticker symbol."""
    query = select(models.FinancialAsset).where(models.FinancialAsset.ticker_symbol == ticker_symbol)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate) -> models.FinancialAsset:
    """
    Creates a new financial asset.
    The asset object maps the inbound 'lastPrice' to 'current_market_price' automatically.
    """
    new_asset_id = str(uuid.uuid4())
    
    db_asset = models.FinancialAsset(
        asset_id=new_asset_id,
        **asset.model_dump(exclude_unset=True, by_alias=False)
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    
    return db_asset

async def update_all_assets_prices(db: AsyncSession) -> Dict[str, Any]:
    """Batch updates all stock prices safely targeting current_market_price."""
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    updated_count = 0
    failed_tickers = []
    
    for asset in assets:
        try:
            new_price = await services.get_stock_price(asset.ticker_symbol)
            if new_price is None:
                failed_tickers.append(asset.ticker_symbol)
                continue
                
            asset.current_market_price = new_price
            asset.last_updated = func.now()
            updated_count += 1
        except Exception as e:
            logger.warning(f"Unexpected error processing {asset.ticker_symbol}: {e}")
            failed_tickers.append(asset.ticker_symbol)
            continue
            
    if updated_count > 0:
        await db.commit()
        
    return {"updated": updated_count, "failed": failed_tickers}