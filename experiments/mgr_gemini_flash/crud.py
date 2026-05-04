from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
import schemas
import uuid
from datetime import datetime

async def get_assets(db: AsyncSession):
    """Pobiera wszystkie aktywa finansowe."""
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    return result.scalars().all()

async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowe aktywo z uwzględnieniem walidacji i czasu aktualizacji.
    Używa asset_id jako klucza głównego.
    """
    db_asset = models.FinancialAsset(
        asset_id=str(uuid.uuid4()),
        ticker_symbol=asset.ticker_symbol,
        last_price=asset.last_price,
        market_cap=asset.market_cap,
        # Jeśli schemat zawiera czas, używamy go, w przeciwnym razie func.now() zadziała w bazie
        last_updated=asset.last_updated if asset.last_updated else datetime.now()
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset