import logging
import sys

def get_logger(name: str = "finance_track") -> logging.Logger:
    """
    Konfiguruje i zwraca logger systemowy, który rejestruje zdarzenia 
    zarówno w pliku 'finance.log', jak i w standardowym wyjściu konsoli.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Zapobiega duplikowaniu handlerów w przypadku wielokrotnego wywołania
    if not logger.handlers:
        # Standardowy format z datą, poziomem błędu i wiadomością
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler zapisujący logi do pliku (z kodowaniem UTF-8)
        file_handler = logging.FileHandler("finance.log", encoding="utf-8")
        file_handler.setFormatter(formatter)

        # Handler wypisujący logi do konsoli
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Inicjalizacja głównego loggera dla aplikacji
logger = get_logger()

def format_market_cap(market_cap: int) -> str:
    """
    Formatuje wartość kapitalizacji rynkowej (market_cap) z typu int 
    do czytelnej postaci tekstowej ze skrótami (np. 'mld', 'mln').
    """
    if market_cap >= 1_000_000_000:
        return f"{market_cap / 1_000_000_000:.2f} mld"
    elif market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f} mln"
    else:
        return str(market_cap)