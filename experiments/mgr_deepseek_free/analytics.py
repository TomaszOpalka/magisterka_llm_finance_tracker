"""
Analytics module for Finance Track.
Provides pure functions for calculating financial indicators:
- Simple Moving Average (SMA)
- Relative Strength Index (RSI)

All calculations are side-effect free and raise descriptive exceptions.
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
    recent_prices = prices[-window:]
    sma = sum(recent_prices) / window
    return round(sma, 4)


def calculate_rsi(prices: List[float], periods: int = 14) -> float:
    """
    Calculate the Relative Strength Index (RSI) for a price series.

    The RSI is computed using the standard Wilder's smoothing method:
        - First average gain/loss is the simple average over the initial `periods`.
        - Subsequent averages are smoothed: avg = (prev_avg * (periods-1) + current) / periods.
        - RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss.

    Args:
        prices: List of closing prices (oldest first).
        periods: The look-back period (default 14).

    Returns:
        RSI value rounded to 2 decimal places, typically between 0 and 100.

    Raises:
        AnalyticsException: If the price list is too short (needs at least periods+1 prices).
    """
    if len(prices) < periods + 1:
        raise AnalyticsException(
            detail=f"Insufficient data for RSI: need at least {periods + 1} prices, got {len(prices)}."
        )

    # Calculate price changes
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Initial average gain and loss over the first `periods` changes
    gains = [d if d > 0 else 0 for d in deltas[:periods]]
    losses = [-d if d < 0 else 0 for d in deltas[:periods]]
    avg_gain = sum(gains) / periods
    avg_loss = sum(losses) / periods

    # Avoid division by zero
    if avg_loss == 0:
        return 100.0

    # Smooth subsequent values
    for i in range(periods, len(deltas)):
        gain = max(deltas[i], 0)
        loss = -min(deltas[i], 0)
        avg_gain = (avg_gain * (periods - 1) + gain) / periods
        avg_loss = (avg_loss * (periods - 1) + loss) / periods

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)