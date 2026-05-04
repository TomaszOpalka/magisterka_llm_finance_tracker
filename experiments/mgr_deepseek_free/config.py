"""
Centralna konfiguracja aplikacji Finance Track.
Wczytuje ustawienia z pliku .env oraz zmiennych środowiskowych.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Ustawienia aplikacji z automatycznym wsparciem dla .env.
    Każdy parametr ma swoją domyślną wartość.
    """

    # Ścieżka do asynchronicznej bazy SQLite (względna lub bezwzględna)
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"

    # Nazwa wyświetlana aplikacji (np. w tytule dokumentacji)
    APP_NAME: str = "Finance Track"

    # Poziom logowania: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",       # Automatyczne wczytywanie zmiennych z pliku .env
        "env_file_encoding": "utf-8",
    }


# Globalna instancja konfiguracji – importowana przez inne moduły
settings = Settings()