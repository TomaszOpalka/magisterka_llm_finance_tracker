"""
CRUD operations for Finance Track.
"""

from datetime import datetime

from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate
from services import get_stock_price
from utils import logger


async def get_assets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    min_price: float | None = None,
    sort_by: str = "ticker_symbol",
):
    """
    Retrieve all financial assets.
    """

    query = select(FinancialAsset)

    if min_price is not None:
        query = query.where(
            FinancialAsset.current_market_price >= min_price
        )

    sortable_fields = {
        "asset_id": FinancialAsset.asset_id,
        "ticker_symbol": FinancialAsset.ticker_symbol,
        "current_market_price": (
            FinancialAsset.current_market_price
        ),
        "market_cap": FinancialAsset.market_cap,
        "last_updated": FinancialAsset.last_updated,
    }

    sort_column = sortable_fields.get(
        sort_by,
        FinancialAsset.ticker_symbol,
    )

    query = (
        query.order_by(asc(sort_column))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)

    return result.scalars().all()


async def get_asset_by_ticker(
    db: AsyncSession,
    ticker_symbol: str,
):
    """
    Retrieve asset by ticker symbol.
    """

    query = select(FinancialAsset).where(
        FinancialAsset.ticker_symbol == ticker_symbol
    )

    result = await db.execute(query)

    return result.scalar_one_or_none()


async def create_asset(
    db: AsyncSession,
    asset: FinancialAssetCreate,
):
    """
    Create a new financial asset.
    """

    db_asset = FinancialAsset(
        ticker_symbol=asset.ticker_symbol,
        current_market_price=asset.current_market_price,
        market_cap=asset.market_cap,
        last_updated=asset.last_updated,
    )

    db.add(db_asset)

    await db.commit()
    await db.refresh(db_asset)

    logger.info(
        "Created asset with asset_id=%s",
        db_asset.asset_id,
    )

    return db_asset


async def update_all_assets_prices(
    db: AsyncSession,
):
    """
    Update all asset prices using yfinance.
    """

    result = await db.execute(
        select(FinancialAsset)
    )

    assets = result.scalars().all()

    updated_assets = 0

    for asset in assets:
        try:
            latest_price = await get_stock_price(
                asset.ticker_symbol
            )

            if latest_price is None:
                logger.warning(
                    "Price update skipped for asset_id=%s",
                    asset.asset_id,
                )
                continue

            asset.current_market_price = latest_price
            asset.last_updated = datetime.utcnow()

            updated_assets += 1

        except Exception as error:
            logger.error(
                (
                    "Synchronization failed for "
                    "asset_id=%s: %s"
                ),
                asset.asset_id,
                error,
            )

    await db.commit()

    logger.info(
        "Updated %s assets successfully",
        updated_assets,
    )

    return updated_assets