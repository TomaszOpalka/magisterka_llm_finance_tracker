import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas


async def get_assets(db: AsyncSession):
    """Pobiera wszystkie instrumenty finansowe."""
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    return result.scalars().all()


async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowy instrument finansowy, zapewniając poprawne nadanie asset_id 
    oraz obsługę daty (last_updated).
    """
    # Ręczne generowanie asset_id
    new_asset_id = str(uuid.uuid4())
    
    # Wykluczamy pola, które nie zostały przekazane (np. domyślne last_updated=None),
    # dzięki czemu SQL sam podłoży func.now() jako server_default
    db_asset = models.FinancialAsset(
        asset_id=new_asset_id,
        **asset.model_dump(exclude_unset=True)
    )
    
    db.add(db_asset)
    await db.commit()
    
    # Odświeżamy model, aby pobrać wygenerowany przez bazę danych czas last_updated
    await db.refresh(db_asset)
    
    return db_asset