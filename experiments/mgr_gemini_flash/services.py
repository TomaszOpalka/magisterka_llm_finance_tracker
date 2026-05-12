import asyncio
import yfinance as yf
from typing import List, Optional
from utils import logger

async def get_stock_price(ticker: str) -> Optional[float]:
    """
    Fetches the current spot price for a given ticker.
    Wraps synchronous yfinance call in a thread to prevent blocking.
    """
    try:
        stock = await asyncio.to_thread(yf.Ticker, ticker)
        
        # 1. Try fast_info first
        data = await asyncio.to_thread(lambda: stock.fast_info.get('last_price'))
        
        # 2. Fallback to history if fast_info is unavailable
        if data is None:
            logger.info(f"FastInfo failed for {ticker}, trying history fallback.")
            hist = await asyncio.to_thread(stock.history, period="1d")
            if not hist.empty:
                data = hist['Close'].iloc[-1]

        if data is None:
            logger.warning(f"Price data unavailable for ticker: {ticker}")
            return None
            
        return float(data)
    except Exception as e:
        logger.error(f"External API error (Price) for {ticker}: {str(e)}")
        return None

async def get_historical_data(ticker: str, days: int = 30) -> List[float]:
    """
    Fetches historical closing prices for the last N days.
    Used primarily for analytical calculations like Moving Averages.
    """
    try:
        stock = await asyncio.to_thread(yf.Ticker, ticker)
        # Fetching history for the specified period
        hist = await asyncio.to_thread(stock.history, period=f"{days}d")
        
        if hist.empty:
            logger.warning(f"No historical data found for {ticker} over {days} days.")
            return []
            
        # Extract 'Close' prices and drop any missing values
        prices = hist['Close'].dropna().tolist()
        return [float(p) for p in prices]
    except Exception as e:
        logger.error(f"External API error (History) for {ticker}: {str(e)}")
        return []