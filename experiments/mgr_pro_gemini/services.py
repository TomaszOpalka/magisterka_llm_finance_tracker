import asyncio
import yfinance as yf
import logging
from typing import List, Optional

logger = logging.getLogger("finance_track")

def _fetch_price_sync(ticker: str) -> float | None:
    """Synchronous helper function to fetch the latest stock price."""
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.last_price
        
        if price is None:
            logger.warning(f"Received None price for ticker: {ticker}")
            return None
            
        return float(price)
    except Exception as e:
        logger.error(f"Error fetching data from yfinance for {ticker}: {e}")
        return None

def _fetch_history_sync(ticker: str, days: int) -> List[float]:
    """Synchronous helper function to fetch historical closing prices."""
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="3mo")
        
        if history.empty:
            logger.warning(f"No historical data found for {ticker}.")
            return []
            
        closes = history['Close'].dropna().tolist()
        return closes[-days:]
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return []

async def get_stock_price(ticker: str) -> float | None:
    """Asynchronously fetches the latest stock price."""
    return await asyncio.to_thread(_fetch_price_sync, ticker)

async def get_historical_data(ticker: str, days: int = 30) -> List[float]:
    """Asynchronously fetches a list of historical closing prices."""
    return await asyncio.to_thread(_fetch_history_sync, ticker, days)