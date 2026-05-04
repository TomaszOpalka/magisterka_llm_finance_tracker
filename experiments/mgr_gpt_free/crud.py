"""
Warstwa CRUD dla systemu Finance Track.
"""

from typing import List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets(db: AsyncSession) -> List[FinancialAsset]:
    """
    Pobiera wszystkie aktywa z bazy danych.
    """
    result = await db.execute(select(FinancialAsset))
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
            # Jeśli last_updated przekazane → użyj, w przeciwnym razie DB ustawi automatycznie
            last_updated=asset_in.last_updated,
        )

        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)

        return new_asset

    except SQLAlchemyError:
        await db.rollback()
        raise