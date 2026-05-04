from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Klasa konfiguracji aplikacji. 
    Automatycznie mapuje zmienne środowiskowe na atrybuty klasy.
    """
    # Adres bazy danych (domyślnie SQLite asynchronicznie)
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"
    
    # Nazwa aplikacji
    APP_NAME: str = "Finance Track"
    
    # Poziom logowania (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"

    # Konfiguracja wczytywania z pliku .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instancja ustawień, którą będziemy importować w innych modułach
settings = Settings()