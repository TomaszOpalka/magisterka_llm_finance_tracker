import logging
import sys

# Konfiguracja loggera
logger = logging.getLogger("finance_track")
logger.setLevel(logging.INFO)

# Formatowanie zapisu (Data - Poziom - Komunikat)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Handler do zapisu w pliku
file_handler = logging.FileHandler("finance.log", encoding="utf-8")
file_handler.setFormatter(formatter)

# Handler do wyświetlania w konsoli
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def format_market_cap(value: int) -> str:
    """
    Formatuje dużą liczbę kapitalizacji rynkowej na skróty 'mln' lub 'mld'.
    """
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} mld"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f} mln"
    return str(value)