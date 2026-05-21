"""
CRUD operations for Finance Track system.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate
from services import get_stock_price


async def get_assets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    sort_by: str = "ticker_symbol",
) -> List[FinancialAsset]:
    """
    Retrieve assets with filtering, pagination and sorting.
    """
    query = select(FinancialAsset)

    if min_price is not None:
        query = query.where(FinancialAsset.last_price >= min_price)

    allowed_sort_fields = {
        "ticker_symbol": FinancialAsset.ticker_symbol,
        "last_price": FinancialAsset.last_price,
        "market_cap": FinancialAsset.market_cap,
        "asset_id": FinancialAsset.asset_id,
    }

    sort_column = allowed_sort_fields.get(
        sort_by,
        FinancialAsset.ticker_symbol,
    )

    query = query.order_by(sort_column).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_asset_by_ticker(
    db: AsyncSession,
    ticker_symbol: str,
) -> Optional[FinancialAsset]:
    """
    Retrieve single asset by ticker symbol.
    """
    result = await db.execute(
        select(FinancialAsset).where(
            FinancialAsset.ticker_symbol == ticker_symbol
        )
    )
    return result.scalars().first()


async def create_asset(
    db: AsyncSession,
    asset_in: FinancialAssetCreate | None = None,
    asset: FinancialAssetCreate | None = None,
) -> FinancialAsset:
    """
    Create new financial asset.
    """
    if asset_in is None:
        asset_in = asset
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


async def update_all_assets_prices(db: AsyncSession) -> int:
    """
    Update prices for all assets using external service.

    Returns number of successfully updated records.
    """
    result = await db.execute(select(FinancialAsset))
    assets = result.scalars().all()

    updated_count = 0

    for asset in assets:
        price = await get_stock_price(asset.ticker_symbol)

        if price is not None:
            asset.last_price = price
            asset.last_updated = datetime.utcnow()
            updated_count += 1

    await db.commit()

    return updated_count