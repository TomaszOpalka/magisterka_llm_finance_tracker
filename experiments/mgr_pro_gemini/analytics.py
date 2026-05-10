import logging
from typing import List, Optional

logger = logging.getLogger("finance_track")

def calculate_moving_average(prices: List[float], period: int = 30) -> Optional[float]:
    """
    Calculates the Simple Moving Average (SMA) for a given list of prices.
    """
    if not prices or len(prices) < period:
        logger.warning(f"Insufficient data for SMA. Required: {period}, Available: {len(prices)}.")
        return None
        
    relevant_prices = prices[-period:]
    sma = sum(relevant_prices) / period
    
    return round(sma, 4)


def calculate_rsi(prices: List[float], periods: int = 14) -> Optional[float]:
    """
    Calculates the Relative Strength Index (RSI) using Wilder's Smoothing Method.
    
    Args:
        prices: A list of historical closing prices.
        periods: The timeframe for the RSI calculation (standard is 14).
        
    Returns:
        The calculated RSI as a float bounded between 0 and 100, rounded to 4 
        decimal places. Returns None if there is insufficient data.
    """
    # RSI requires at least (periods + 1) data points to calculate price differences
    if not prices or len(prices) < periods + 1:
        logger.warning(f"Insufficient data for RSI. Required: {periods + 1}, Available: {len(prices)}.")
        return None

    gains = []
    losses = []

    # Step 1: Calculate period-to-period price changes
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    # Step 2: Calculate the initial Simple Moving Average of gains and losses
    avg_gain = sum(gains[:periods]) / periods
    avg_loss = sum(losses[:periods]) / periods

    # Step 3: Apply Wilder's Smoothing Method for the remaining periods
    for i in range(periods, len(gains)):
        avg_gain = ((avg_gain * (periods - 1)) + gains[i]) / periods
        avg_loss = ((avg_loss * (periods - 1)) + losses[i]) / periods

    # Step 4: Calculate the Relative Strength (RS) and RSI
    if avg_loss == 0:
        # Edge case: If average loss is 0, the asset only went up. RSI maxes out at 100.
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return round(rsi, 4)