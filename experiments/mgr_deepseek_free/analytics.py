"""
Analytics module for Finance Track.
Provides financial calculators such as moving averages.
All calculations are pure functions (no I/O).
"""

from typing import List
from exceptions import AnalyticsException


def calculate_moving_average(prices: List[float], window: int = 30) -> float:
    """
    Calculate the simple moving average (SMA) of a price series.

    Args:
        prices: List of closing prices (oldest first).
        window: The rolling window size (default 30).

    Returns:
        The SMA of the last `window` prices, rounded to 4 decimal places.

    Raises:
        AnalyticsException: If there are fewer prices than the window size.
    """
    if len(prices) < window:
        raise AnalyticsException(
            detail=f"Insufficient data: need at least {window} prices, got {len(prices)}."
        )
    # Use the most recent `window` prices
    recent_prices = prices[-window:]
    sma = sum(recent_prices) / window
    return round(sma, 4)