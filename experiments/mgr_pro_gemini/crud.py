from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
import models
import services
import logging

logger = logging.getLogger("finance_track")

async def update_all_assets_prices(db: AsyncSession) -> dict:
    """
    Iterates through all assets, fetches the latest price, and updates the database.
    Designed for error resilience: skips failures and continues batch processing.
    """
    query = select(models.FinancialAsset)
    result = await db.execute(query)
    assets = result.scalars().all()
    
    updated_count = 0
    failed_tickers = []
    
    for asset in assets:
        try:
            new_price = await services.get_stock_price(asset.ticker_symbol)
            
            # Error Resilience: Log warning and continue if data is missing
            if new_price is None:
                logger.warning(f"Failed to fetch price for {asset.ticker_symbol}. Skipping to next asset.")
                failed_tickers.append(asset.ticker_symbol)
                continue
                
            asset.last_price = new_price
            asset.last_updated = func.now()
            updated_count += 1
            
        except Exception as e:
            # Catch unexpected library crashes (e.g., empty DataFrame logic failures)
            logger.warning(f"Unexpected error while processing {asset.ticker_symbol}: {e}")
            failed_tickers.append(asset.ticker_symbol)
            continue
            
    if updated_count > 0:
        await db.commit()
        
    return {"updated": updated_count, "failed": failed_tickers}