import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc

import models
import schemas
from services import get_stock_price
from utils import logger

async def get_assets(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    min_price: float = None, 
    sort_by: str = "ticker_symbol"
):
    """
    Retrieves a list of financial assets with support for pagination, 
    price filtering, and dynamic sorting.
    """
    query = select(models.FinancialAsset)

    # Filtering by minimum price
    if min_price is not None:
        query = query.where(models.FinancialAsset.last_price >= min_price)

    # Dynamic sorting
    if hasattr(models.FinancialAsset, sort_by):
        column = getattr(models.FinancialAsset, sort_by)
        query = query.order_by(column)
    else:
        query = query.order_by(models.FinancialAsset.ticker_symbol)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_asset_by_ticker(db: AsyncSession, ticker: str):
    """
    Retrieves a single asset record by its unique ticker symbol.
    """
    query = select(models.FinancialAsset).where(
        models.FinancialAsset.ticker_symbol == ticker.upper()
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Creates a new financial asset. 
    Explicitly generates a UUID for asset_id to fulfill the primary key requirement.
    """
    db_asset = models.FinancialAsset(
        asset_id=str(uuid.uuid4()),
        ticker_symbol=asset.ticker_symbol.upper(),
        last_price=asset.last_price,
        market_cap=asset.market_cap,
        last_updated=datetime.now()
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset

async def update_all_assets_prices(db: AsyncSession) -> int:
    """
    Iterates through all assets and updates their current market price 
    via the external Stock Service.
    """
    result = await db.execute(select(models.FinancialAsset))
    assets = result.scalars().all()
    
    updated_count = 0
    for asset in assets:
        new_price = await get_stock_price(asset.ticker_symbol)
        if new_price:
            asset.last_price = new_price
            asset.last_updated = datetime.now()
            updated_count += 1
            
    await db.commit()
    return updated_count