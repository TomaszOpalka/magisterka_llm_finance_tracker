from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Klasa konfiguracyjna aplikacji Finance Track.
    Wczytuje zmienne z pliku .env, a w przypadku ich braku ustawia wartości domyślne.
    """
    # Główny adres połączeniowy do bazy danych
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"
    
    # Nazwa aplikacji, przydatna np. w logach lub dokumentacji FastAPI
    APP_NAME: str = "Finance Track"
    
    # Globalny poziom logowania (np. INFO, DEBUG, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"

    # Konfiguracja wczytywania pliku .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Inicjalizacja globalnego obiektu konfiguracyjnego.
# Wywołanie tej klasy automatycznie przeskanuje środowisko oraz plik .env.
settings = Settings()