import logging
from typing import List, Optional

logger = logging.getLogger("finance_track")

def calculate_moving_average(prices: List[float], period: int = 30) -> Optional[float]:
    """
    Calculates the Simple Moving Average (SMA) for a given list of prices.
    
    Args:
        prices: A list of historical closing prices.
        period: The number of days to calculate the average over.
        
    Returns:
        The SMA as a float rounded to 4 decimal places, or None if there 
        is insufficient data to perform the calculation.
    """
    if not prices:
        logger.warning("Empty price list provided for SMA calculation.")
        return None
        
    if len(prices) < period:
        logger.warning(
            f"Insufficient data for SMA. Required: {period}, Available: {len(prices)}."
        )
        return None
        
    # Extract the exact window of prices required for the period
    relevant_prices = prices[-period:]
    
    # Mathematically sound calculation: sum of prices divided by the period count
    sma = sum(relevant_prices) / period
    
    # Round to 4 decimal places for standard financial precision
    return round(sma, 4)