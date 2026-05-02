"""
Moduł pomocniczy dla systemu Finance Track.
Zawiera konfigurację loggera oraz funkcje pomocnicze.
"""

import logging
from logging.handlers import RotatingFileHandler


def setup_logger() -> logging.Logger:
    """
    Konfiguracja loggera aplikacji.

    Logger zapisuje logi do pliku finance.log oraz wyświetla je w konsoli.
    """
    logger = logging.getLogger("finance_track")
    logger.setLevel(logging.INFO)

    # Format komunikatów logów
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Handler do zapisu w pliku (rotacja pliku)
    file_handler = RotatingFileHandler(
        "finance.log",
        maxBytes=1_000_000,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)

    # Handler do wyświetlania w konsoli
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Unikamy dodawania handlerów wielokrotnie
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Inicjalizacja loggera
logger = setup_logger()


def format_market_cap(value: int | None) -> str:
    """
    Formatuje wartość market_cap do czytelnej postaci tekstowej.

    :param value: Kapitalizacja rynkowa
    :return: Sformatowany tekst (np. 1.5 mld)
    """
    if value is None:
        return "brak danych"

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} mld"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} mln"
    if value >= 1_000:
        return f"{value / 1_000:.2f} tys."

    return str(value)