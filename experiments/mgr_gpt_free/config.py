"""
Moduł konfiguracji aplikacji Finance Track.
Wykorzystuje pydantic-settings do zarządzania ustawieniami.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Klasa przechowująca konfigurację aplikacji.

    Wartości mogą być nadpisywane przez zmienne środowiskowe
    lub plik .env.
    """

    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"
    APP_NAME: str = "Finance Track"
    LOG_LEVEL: str = "INFO"

    # Konfiguracja Pydantic Settings (ładowanie z pliku .env)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Instancja ustawień używana w całej aplikacji
settings = Settings()