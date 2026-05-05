from typing import List, Optional

def calculate_moving_average(prices: List[float]) -> Optional[float]:
    """
    Calculates the Simple Moving Average (SMA).
    Returns None if the list is empty or data is insufficient.
    """
    if not prices:
        return None
    
    total = sum(prices)
    count = len(prices)
    
    # Mathematical average calculation
    sma = total / count
    return round(sma, 2)