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

# Allowed fields for dynamic sorting – internal column names (snake_case)
ALLOWED_SORT_FIELDS = {
    "asset_id",
    "ticker_symbol",
    "current_market_price",
    "market_cap",
    "last_updated",
}


async def get_assets(
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    sort_by: Optional[str] = "ticker_symbol",
) -> list[FinancialAsset]:
    """
    Retrieve assets with optional filtering, sorting, and pagination.

    Args:
        skip: Records to skip (default 0).
        limit: Maximum records to return (default 10, max 100).
        min_price: Optional minimum price filter (applied to current_market_price).
        sort_by: Column to sort ascending (allowed: asset_id, ticker_symbol,
                 current_market_price, market_cap, last_updated).

    Returns:
        List of FinancialAsset ORM objects.
    """
    async with async_session() as session:
        query = select(FinancialAsset)

        if min_price is not None:
            query = query.where(FinancialAsset.current_market_price >= min_price)

        # Safe dynamic ordering
        sort_by = sort_by if sort_by in ALLOWED_SORT_FIELDS else "ticker_symbol"
        column = getattr(FinancialAsset, sort_by)
        query = query.order_by(asc(column)).offset(skip).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


async def get_asset_by_ticker(ticker_symbol: str) -> Optional[FinancialAsset]:
    """
    Fetch a single asset by its ticker symbol.

    Args:
        ticker_symbol: Stock symbol (unique).

    Returns:
        FinancialAsset if found, else None.
    """
    async with async_session() as session:
        result = await session.execute(
            select(FinancialAsset).where(FinancialAsset.ticker_symbol == ticker_symbol)
        )
        return result.scalars().first()


async def create_asset(asset_data: FinancialAssetCreate) -> FinancialAsset:
    """
    Create a new financial asset record.

    Args:
        asset_data: Validated Pydantic schema (internal attr: current_market_price).

    Returns:
        The newly created FinancialAsset object.

    Raises:
        ValueError: If integrity is violated (e.g., duplicate ticker).
    """
    new_id = str(uuid.uuid4())

    async with async_session() as session:
        asset = FinancialAsset(
            asset_id=new_id,
            ticker_symbol=asset_data.ticker_symbol,
            current_market_price=asset_data.current_market_price,
            market_cap=asset_data.market_cap,
            last_updated=asset_data.last_updated,
        )
        session.add(asset)
        try:
            await session.commit()
            await session.refresh(asset)
            logger.info(f"Created asset {asset.asset_id} ({asset.ticker_symbol}).")
            return asset
        except IntegrityError as exc:
            await session.rollback()
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