"""
Application configuration module for Finance Track.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings.
    """

    DATABASE_URL: str = (
        "sqlite+aiosqlite:///./finance.db"
    )

    APP_NAME: str = "Finance Track"

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()