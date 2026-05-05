"""
Service layer for external stock data integration.
"""

import asyncio
from typing import Optional

import yfinance as yf


class StockServiceException(Exception):
    """
    Custom exception for stock data service errors.
    """
    pass


def _fetch_price_sync(ticker: str) -> Optional[float]:
    """
    Synchronous function to fetch stock price using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])

    except Exception:
        return None


async def get_stock_price(ticker: str) -> Optional[float]:
    """
    Asynchronous wrapper for fetching stock price.

    Uses asyncio.to_thread to avoid blocking the event loop.
    """
    try:
        price = await asyncio.to_thread(_fetch_price_sync, ticker)
        return price

    except Exception as exc:
        raise StockServiceException(
            f"Failed to fetch price for ticker {ticker}"
        ) from exc