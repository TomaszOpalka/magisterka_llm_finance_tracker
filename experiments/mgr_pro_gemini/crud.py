import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas


async def get_assets(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    min_price: float | None = None, 
    sort_by: str = "ticker_symbol"
):
    """
    Pobiera instrumenty finansowe z bazy danych z uwzględnieniem
    filtrowania (min_price), paginacji (skip, limit) oraz sortowania (sort_by).
    """
    # Inicjalizacja bazowego zapytania
    query = select(models.FinancialAsset)
    
    # Zastosowanie opcjonalnego filtru minimalnej ceny
    if min_price is not None:
        query = query.where(models.FinancialAsset.last_price >= min_price)
        
    # Bezpieczne mapowanie parametrów sortowania na kolumny modelu.
    # Weryfikacja: Zapewniono obsługę 'asset_id' jako klucza głównego.
    sort_options = {
        "asset_id": models.FinancialAsset.asset_id,
        "ticker_symbol": models.FinancialAsset.ticker_symbol,
        "last_price": models.FinancialAsset.last_price,
        "market_cap": models.FinancialAsset.market_cap,
        "last_updated": models.FinancialAsset.last_updated
    }
    
    # Wybór kolumny do sortowania (zabezpieczenie: fallback do ticker_symbol)
    sort_column = sort_options.get(sort_by, models.FinancialAsset.ticker_symbol)
    
    # Zastosowanie sortowania i paginacji (offset/limit)
    query = query.order_by(sort_column).offset(skip).limit(limit)
    
    # Wykonanie asynchronicznego zapytania
    result = await db.execute(query)
    
    return result.scalars().all()


async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowy instrument finansowy.
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