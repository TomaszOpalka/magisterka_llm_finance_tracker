"""
Service layer for external stock data integration.
"""

import asyncio
from typing import Optional, List

import yfinance as yf


class StockServiceException(Exception):
    """
    Custom exception for stock data service errors.
    """
    pass


def _fetch_price_sync(ticker: str) -> Optional[float]:
    """
    Synchronous function to fetch stock price.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])

    except Exception:
        return None


def _fetch_history_sync(ticker: str, days: int) -> List[float]:
    """
    Synchronous function to fetch historical closing prices.
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=f"{days}d")

        if data.empty:
            return []

        return [float(x) for x in data["Close"].tolist()]

    except Exception:
        return []


async def get_stock_price(ticker: str) -> Optional[float]:
    """
    Async wrapper for fetching current stock price.
    """
    try:
        return await asyncio.to_thread(_fetch_price_sync, ticker)
    except Exception as exc:
        raise StockServiceException(str(exc)) from exc


async def get_historical_data(
    ticker: str,
    days: int = 30,
) -> List[float]:
    """
    Async function to fetch historical prices using threads.
    """
    try:
        data = await asyncio.to_thread(_fetch_history_sync, ticker, days)

        if not data:
            raise StockServiceException(
                f"No historical data for ticker {ticker}"
            )

        return data

    except Exception as exc:
        raise StockServiceException(str(exc)) from exc