from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
import schemas
import uuid

async def get_assets(db: AsyncSession):
    """
    Pobiera wszystkie aktywa finansowe z bazy danych.
    """
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    # Zwracamy listę obiektów
    return result.scalars().all()

async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowy rekord aktywa finansowego.
    Generuje unikalny asset_id przed zapisem.
    """
    # Generowanie unikalnego identyfikatora asset_id
    db_asset = models.FinancialAsset(
        asset_id=str(uuid.uuid4()),
        ticker_symbol=asset.ticker_symbol,
        last_price=asset.last_price,
        market_cap=asset.market_cap
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset