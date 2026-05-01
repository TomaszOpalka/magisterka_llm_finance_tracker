"""
Moduł CRUD – operacje bazodanowe dla tabeli financial_assets.
Wszystkie funkcje działają asynchronicznie.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets(db: AsyncSession):
    """
    Pobiera listę wszystkich aktywów finansowych z bazy danych.
    """
    result = await db.execute(select(FinancialAsset))
    return result.scalars().all()


async def create_asset(db: AsyncSession, asset: FinancialAssetCreate):
    """
    Tworzy nowe aktywo finansowe w bazie danych.
    """
    # Tworzenie nowego obiektu modelu SQLAlchemy
    db_asset = FinancialAsset(
        asset_id=asset.ticker_symbol,   # Używamy ticker_symbol jako asset_id (można zmienić logikę)
        ticker_symbol=asset.ticker_symbol,
        last_price=asset.last_price,
        market_cap=asset.market_cap
    )

    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)

    return db_asset