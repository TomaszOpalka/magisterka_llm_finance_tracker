import logging
from typing import List, Optional

logger = logging.getLogger("finance_track")

def calculate_moving_average(prices: List[float], period: int = 30) -> Optional[float]:
    """Calculates the Simple Moving Average (SMA)."""
    if not prices or len(prices) < period:
        logger.warning(f"SMA calculation failed. Required: {period}, provided: {len(prices)}")
        return None
        
    relevant_prices = prices[-period:]
    sma = sum(relevant_prices) / period
    return round(sma, 4)

def calculate_rsi(prices: List[float], periods: int = 14) -> Optional[float]:
    """Calculates the Relative Strength Index (RSI) using Wilder's Smoothing."""
    if not prices or len(prices) < periods + 1:
        logger.warning(f"RSI calculation failed. Required: {periods + 1}, provided: {len(prices)}")
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    avg_gain = sum(gains[:periods]) / periods
    avg_loss = sum(losses[:periods]) / periods

    for i in range(periods, len(gains)):
        avg_gain = ((avg_gain * (periods - 1)) + gains[i]) / periods
        avg_loss = ((avg_loss * (periods - 1)) + losses[i]) / periods

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return round(rsi, 4)