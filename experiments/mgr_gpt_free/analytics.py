"""
Analytics module for financial calculations.
"""

from typing import List, Optional


def calculate_moving_average(prices: List[float]) -> Optional[float]:
    """
    Calculate simple moving average (SMA).

    Returns None if insufficient data.
    """
    if not prices:
        return None

    if len(prices) == 0:
        return None

    return sum(prices) / len(prices)