"""
Analytics module for financial calculations.
"""

from typing import List, Optional


def calculate_moving_average(prices: List[float]) -> Optional[float]:
    """
    Calculate simple moving average (SMA).
    """
    if not prices:
        return None

    return round(sum(prices) / len(prices), 2)


def calculate_rsi(
    prices: List[float],
    periods: int = 14,
) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).

    RSI formula:
    RSI = 100 - (100 / (1 + RS))

    RS = average_gain / average_loss
    """
    if len(prices) <= periods:
        return None

    gains: List[float] = []
    losses: List[float] = []

    # Calculate price changes
    for index in range(1, len(prices)):
        delta = prices[index] - prices[index - 1]

        if delta > 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))

    # Initial averages
    avg_gain = sum(gains[:periods]) / periods
    avg_loss = sum(losses[:periods]) / periods

    # Prevent division by zero
    if avg_loss == 0:
        return 100.0

    # Smoothed RSI calculation
    for index in range(periods, len(gains)):
        avg_gain = (
            (avg_gain * (periods - 1)) + gains[index]
        ) / periods

        avg_loss = (
            (avg_loss * (periods - 1)) + losses[index]
        ) / periods

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)