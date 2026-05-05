"""
Warstwa CRUD dla systemu Finance Track.
"""

from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    sort_by: str = "ticker_symbol",
) -> List[FinancialAsset]:
    """
    Pobiera aktywa z bazy danych z filtrowaniem, paginacją i sortowaniem.
    """
    # Budowa zapytania bazowego
    query = select(FinancialAsset)

    # Filtrowanie po minimalnej cenie
    if min_price is not None:
        query = query.where(FinancialAsset.last_price >= min_price)

    # Obsługa sortowania (bezpieczna lista pól)
    allowed_sort_fields = {
        "ticker_symbol": FinancialAsset.ticker_symbol,
        "last_price": FinancialAsset.last_price,
        "market_cap": FinancialAsset.market_cap,
        "asset_id": FinancialAsset.asset_id,
    }

    sort_column = allowed_sort_fields.get(
        sort_by,
        FinancialAsset.ticker_symbol,  # domyślnie
    )

    query = query.order_by(sort_column)

    # Paginacja
    query = query.offset(skip).limit(limit)

    # Wykonanie zapytania
    result = await db.execute(query)
    return result.scalars().all()


async def create_asset(
    db: AsyncSession,
    asset_in: FinancialAssetCreate,
) -> FinancialAsset:
    """
    Tworzy nowe aktywo finansowe.
    """
    try:
        new_asset = FinancialAsset(
            asset_id=str(uuid4()),
            ticker_symbol=asset_in.ticker_symbol,
            last_price=asset_in.last_price,
            market_cap=asset_in.market_cap,
            last_updated=asset_in.last_updated,
        )

        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)

        return new_asset

    except SQLAlchemyError:
        await db.rollback()
        raise