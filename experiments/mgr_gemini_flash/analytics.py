from typing import List, Optional

def calculate_moving_average(prices: List[float]) -> Optional[float]:
    if not prices:
        return None
    return round(sum(prices) / len(prices), 2)

def calculate_rsi(prices: List[float], periods: int = 14) -> Optional[float]:
    """
    Calculates the Relative Strength Index (RSI).
    Requires at least periods + 1 data points.
    """
    if len(prices) <= periods:
        return None

    deltas = []
    for i in range(len(prices) - 1):
        deltas.append(prices[i+1] - prices[i])

    gains = [d if d > 0 else 0 for d in deltas]
    losses = [abs(d) if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:periods]) / periods
    avg_loss = sum(losses[:periods]) / periods

    if avg_loss == 0:
        return 100.0

    # Standard RSI formula: 100 - (100 / (1 + RS))
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)