import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas


async def get_assets(db: AsyncSession):
    """Pobiera wszystkie instrumenty finansowe z bazy danych."""
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    return result.scalars().all()


async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowy instrument finansowy, przypisując prawidłowy asset_id 
    i pozwalając bazie danych obsłużyć domyślne last_updated.
    """
    # Gwarantujemy użycie właściwego klucza
    new_asset_id = str(uuid.uuid4())
    
    db_asset = models.FinancialAsset(
        asset_id=new_asset_id,
        **asset.model_dump(exclude_unset=True)
    )
    
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    
    return db_asset