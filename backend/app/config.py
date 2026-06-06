"""Application configuration via pydantic-settings.

Reads from .env file at the project root. All values can be overridden
via environment variables (e.g., DATABASE_URL in docker-compose.yml).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env and environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    DEBUG: bool = False
    SECRET_KEY: str
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]


settings = Settings()
