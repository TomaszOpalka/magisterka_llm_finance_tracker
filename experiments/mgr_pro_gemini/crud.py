import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

import models
import schemas
import services


async def get_assets(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    min_price: float | None = None, 
    sort_by: str = "ticker_symbol"
) -> List[models.FinancialAsset]:
    """
    Retrieves all financial assets from the database with pagination,
    filtering, and safe sorting.
    """
    query = select(models.FinancialAsset)
    
    if min_price is not None:
        query = query.where(models.FinancialAsset.last_price >= min_price)
        
    sort_options = {
        "asset_id": models.FinancialAsset.asset_id,
        "ticker_symbol": models.FinancialAsset.ticker_symbol,
        "last_price": models.FinancialAsset.last_price,
        "market_cap": models.FinancialAsset.market_cap,
        "last_updated": models.FinancialAsset.last_updated
    }
    
    sort_column = sort_options.get(sort_by, models.FinancialAsset.ticker_symbol)
    query = query.order_by(sort_column).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_asset_by_ticker(db: AsyncSession, ticker_symbol: str) -> models.FinancialAsset | None:
    """
    Retrieves a single financial asset by its unique ticker symbol.
    """
    query = select(models.FinancialAsset).where(models.FinancialAsset.ticker_symbol == ticker_symbol)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate) -> models.FinancialAsset:
    """
    Creates a new financial asset using a generated asset_id.
    """
    new_asset_id = str(uuid.uuid4())
    
    db_asset = models.FinancialAsset(
        asset_id=new_asset_id,
        **asset.model_dump(exclude_unset=True)
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    
    return db_asset


async def update_all_assets_prices(db: AsyncSession) -> int:
    """
    Iterates through all assets in the database, fetches the latest price
    using the external yfinance service, and updates the database.
    Commits all changes at the end of the batch operation.
    """
    # Fetch all assets without pagination limits for the batch sync
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    updated_count = 0
    
    for asset in assets:
        new_price = await services.get_stock_price(asset.ticker_symbol)
        
        if new_price is not None:
            asset.last_price = new_price
            # Update the timestamp using SQLAlchemy's func.now()
            asset.last_updated = func.now()
            updated_count += 1
            
    # Commit all the updated prices in a single batch transaction
    if updated_count > 0:
        await db.commit()
        
    return updated_count