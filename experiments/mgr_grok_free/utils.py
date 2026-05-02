"""
Moduł pomocniczy (utils) dla systemu Finance Track.
Zawiera konfigurację logowania oraz funkcje formatujące.
"""

import logging
import sys
from typing import Optional


# ==================== KONFIGURACJA LOGGERA ====================

logger = logging.getLogger("finance_track")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler do pliku
file_handler = logging.FileHandler("finance.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler do konsoli
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# ==================== FUNKCJE POMOCNICZE ====================

def format_market_cap(market_cap: Optional[int]) -> str:
    """
    Formatuje wartość kapitalizacji rynkowej do czytelnej postaci.
    Przykład: 1500000000 → "1.5 mld"
    """
    if market_cap is None:
        return "Brak danych"

    if market_cap >= 1_000_000_000:
        return f"{market_cap / 1_000_000_000:.2f} mld"
    elif market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f} mln"
    elif market_cap >= 1_000:
        return f"{market_cap / 1_000:.1f} tys."
    else:
        return str(market_cap)