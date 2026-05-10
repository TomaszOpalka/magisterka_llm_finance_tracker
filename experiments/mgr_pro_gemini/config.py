from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configuration managed via environment variables.
    Defaults to the ./data directory to support Docker volume mounts
    and ensure data persistence.
    """
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/finance.db"
    APP_NAME: str = "Finance Track"
    LOG_LEVEL: str = "INFO"

    # Configures Pydantic to read from a .env file if it exists,
    # and ignores any extra variables found in the environment.
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# Instantiate the settings object to be imported across the application
settings = Settings()