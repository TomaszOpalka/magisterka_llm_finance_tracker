import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List, Optional
import models
import schemas
import services
from utils import logger

async def get_assets(db: AsyncSession, skip: int = 0, limit: int = 10) -> List[models.FinancialAsset]:
    """Retrieves localized registry records out of the tracking entity map."""
    query = select(models.FinancialAsset).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_asset_by_ticker(db: AsyncSession, ticker_symbol: str) -> Optional[models.FinancialAsset]:
    """Retrieves an individual asset record matching an uppercase target ticker."""
    query = select(models.FinancialAsset).where(models.FinancialAsset.ticker_symbol == ticker_symbol.upper())
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_asset(db: AsyncSession, asset_schema: schemas.FinancialAssetCreate) -> models.FinancialAsset:
    """
    Accepts Pydantic verification metrics and persists them to the storage layer.
    Upholds system isolation rules by mapping schema inputs to current_market_price.
    Generates string asset_id to supply client assetId.
    """
    db_asset = models.FinancialAsset(
        asset_id=str(uuid.uuid4()),
        ticker_symbol=asset_schema.ticker_symbol.upper(),
        current_market_price=asset_schema.current_market_price,
        market_cap=asset_schema.market_cap
    )
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset

async def update_all_assets_prices(db: AsyncSession) -> int:
    """
    Scans stored asset entities, executes asynchronous queries to pull live
    market updates, and persists findings to current_market_price fields.
    """
    logger.info("Executing global bulk pricing update task.")
    assets = await get_assets(db, skip=0, limit=1000)
    updated_records = 0

    for asset in assets:
        fresh_price = await services.get_stock_price(asset.ticker_symbol)
        if fresh_price is not None:
            query = (
                update(models.FinancialAsset)
                .where(models.FinancialAsset.asset_id == asset.asset_id)
                .values(current_market_price=fresh_price)
            )
            await db.execute(query)
            updated_records += 1

    await db.commit()
    logger.info(f"Price updates committed successfully. Updated lines: {updated_records}")
    return updated_records