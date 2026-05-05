import asyncio
import yfinance as yf
from typing import Optional
from utils import logger

async def get_stock_price(ticker: str) -> Optional[float]:
    """
    Fetches the current stock price using yfinance.
    Wraps synchronous call in a thread to avoid blocking the event loop.
    """
    try:
        # Running synchronous yfinance call in a separate thread
        stock = await asyncio.to_thread(yf.Ticker, ticker)
        data = await asyncio.to_thread(stock.fast_info.get, 'last_price')
        
        if data is None:
            logger.warning(f"Could not find price data for ticker: {ticker}")
            return None
            
        return float(data)
    except Exception as e:
        logger.error(f"External API error for {ticker}: {str(e)}")
        return None