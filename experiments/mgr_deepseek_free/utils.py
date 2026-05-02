"""
Narzędzia pomocnicze dla systemu Finance Track.
Zawiera konfigurację loggera oraz funkcję formatującą kapitalizację rynkową.
"""

import logging

# ---------- Konfiguracja Loggera ----------

def _configure_logger() -> logging.Logger:
    """
    Tworzy i konfiguruje logger dla całej aplikacji.
    Zdarzenia zapisywane są jednocześnie do pliku finance.log i konsoli.
    """
    logger = logging.getLogger("finance_track")
    logger.setLevel(logging.INFO)

    # Unikamy duplikowania handlerów przy wielokrotnym imporcie
    if not logger.handlers:
        # Format komunikatu: data, poziom, nazwa modułu, treść
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Handler do pliku
        file_handler = logging.FileHandler("finance.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler konsoli
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


# Globalna instancja loggera, importowana przez inne moduły
logger = _configure_logger()


# ---------- Funkcja formatująca kapitalizację rynkową ----------

def format_market_cap(value: int) -> str:
    """
    Przekształca liczbową wartość kapitalizacji rynkowej na czytelny tekst.

    Argumenty:
        value: Kapitalizacja jako liczba całkowita (np. 1_500_000_000).

    Zwraca:
        String z zaokrągloną wartością i przyrostkiem (mld/mln/tys.).
        Przykłady: 2500000000 -> '2.5 mld', 1500000 -> '1.5 mln'.
    """
    if value >= 1_000_000_000:
        result = value / 1_000_000_000
        return f"{result:.1f} mld"
    elif value >= 1_000_000:
        result = value / 1_000_000
        return f"{result:.1f} mln"
    elif value >= 1_000:
        result = value / 1_000
        return f"{result:.1f} tys."
    else:
        return str(value)