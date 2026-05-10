from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings mapped to environment variables.
    Defaults are used if variables are not provided in the shell or .env file.
    """
    # DATABASE_URL should point to /app/data/finance.db in Docker
    DATABASE_URL: str = "sqlite+aiosqlite:///./finance.db"
    APP_NAME: str = "Finance Track API"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()