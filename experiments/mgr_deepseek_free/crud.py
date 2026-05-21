"""
CRUD operations for the financial_assets table.
Uses async SQLAlchemy sessions, Pydantic schemas, and external services.
All internal field references now use current_market_price.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, asc
from sqlalchemy.exc import IntegrityError

from database import async_session
from models import FinancialAsset
from schemas import FinancialAssetCreate
from services import get_stock_price
from utils import logger

from sqlalchemy.ext.asyncio import AsyncSession

# Allowed fields for dynamic sorting – internal column names (snake_case)
ALLOWED_SORT_FIELDS = {
    "asset_id",
    "ticker_symbol",
    "current_market_price",
    "market_cap",
    "last_updated",
}


async def get_assets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    sort_by: Optional[str] = "ticker_symbol",
) -> list[FinancialAsset]:
    """
    Retrieve assets with optional filtering, sorting, and pagination.
    """
    query = select(FinancialAsset)

    if min_price is not None:
        query = query.where(FinancialAsset.current_market_price >= min_price)

    # Safe dynamic ordering
    sort_by = sort_by if sort_by in ALLOWED_SORT_FIELDS else "ticker_symbol"
    column = getattr(FinancialAsset, sort_by)
    query = query.order_by(asc(column)).offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_asset_by_ticker(db: AsyncSession, ticker_symbol: str) -> Optional[FinancialAsset]:
    """
    Fetch a single asset by its ticker symbol.
    """
    result = await db.execute(
        select(FinancialAsset).where(FinancialAsset.ticker_symbol == ticker_symbol)
    )
    return result.scalars().first()


async def create_asset(db: AsyncSession, asset_data: FinancialAssetCreate) -> FinancialAsset:
    """
    Create a new financial asset record.
    """
    new_id = str(uuid.uuid4())

    asset = FinancialAsset(
        asset_id=new_id,
        ticker_symbol=asset_data.ticker_symbol,
        current_market_price=asset_data.current_market_price,
        market_cap=asset_data.market_cap,
        last_updated=asset_data.last_updated,
    )
    db.add(asset)
    try:
        await db.commit()
        await db.refresh(asset)
        logger.info(f"Created asset {asset.asset_id} ({asset.ticker_symbol}).")
        return asset
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(
            f"Cannot create asset: '{asset_data.ticker_symbol}' may already exist."
        ) from exc


async def update_all_assets_prices(db) -> dict:
    """
    Update the current_market_price and last_updated for all assets
    using live stock data from an external service.

    Args:
        db: Async SQLAlchemy session.

    Returns:
        Dictionary with counts of updated, skipped, and failed assets.
    """
    result = await db.execute(select(FinancialAsset))
    assets = result.scalars().all()

    updated = 0
    skipped = 0
    failed = 0

    for asset in assets:
        try:
            new_price = await get_stock_price(asset.ticker_symbol)
            if new_price is not None:
                asset.current_market_price = new_price
                asset.last_updated = datetime.now(timezone.utc)
                updated += 1
                logger.debug(
                    f"Updated {asset.ticker_symbol} -> {new_price}"
                )
            else:
                logger.warning(
                    f"No price data for {asset.ticker_symbol} (asset_id={asset.asset_id}); skipped."
                )
                skipped += 1
        except Exception as e:
            logger.error(
                f"Failed to update {asset.ticker_symbol} (asset_id={asset.asset_id}): {e}"
            )
            failed += 1

    if updated > 0 or failed == 0:
        await db.commit()
        logger.info(
            f"Batch update: {updated} updated, {skipped} skipped, {failed} failed."
        )
    else:
        await db.rollback()
        logger.warning("All updates failed – rolling back to preserve previous prices.")

    return {"updated": updated, "skipped": skipped, "failed": failed}