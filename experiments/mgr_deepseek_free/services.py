"""
External services for the Finance Track system.
Wraps yfinance (synchronous) in asyncio.to_thread to avoid blocking the event loop.
"""

import asyncio
import yfinance as yf
from exceptions import StockDataException
from utils import logger


async def get_stock_price(ticker: str) -> float | None:
    """
    Retrieve the latest closing price for a given stock ticker asynchronously.

    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'GOOGL').

    Returns:
        The latest closing price as a float, or None if data is not available.

    Raises:
        StockDataException: If the ticker is invalid or the API call fails.
    """
    try:
        # yfinance is synchronous – run it in a thread to avoid blocking
        stock = await asyncio.to_thread(yf.Ticker, ticker)
        # Fetch 5-day history to ensure we get at least one valid closing price
        hist = await asyncio.to_thread(stock.history, period="5d")
        if hist.empty:
            logger.warning(f"No price data found for ticker {ticker}.")
            return None
        latest_price = hist["Close"].iloc[-1]
        logger.info(f"Fetched price for {ticker}: {latest_price}")
        return float(latest_price)
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        raise StockDataException(
            detail=f"Unable to retrieve data for '{ticker}'. The symbol may be invalid or the market is closed."
        ) from e