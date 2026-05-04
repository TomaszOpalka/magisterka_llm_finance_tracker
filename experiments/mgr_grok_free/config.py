"""
Moduł konfiguracji aplikacji Finance Track.
Używa Pydantic Settings (v2) do ładowania ustawień z pliku .env oraz wartości domyślnych.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Główna klasa konfiguracyjna systemu Finance Track.
    Automatycznie wczytuje zmienne z pliku .env (jeśli istnieje).
    """

    # Konfiguracja bazy danych
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"

    # Nazwa aplikacji
    APP_NAME: str = "Finance Track"

    # Poziom logowania
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Instancja ustawień (singleton)
settings = Settings()