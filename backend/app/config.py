"""Application configuration via pydantic-settings.

Reads from .env file at the project root. All values can be overridden
via environment variables (e.g., DATABASE_URL in docker-compose.yml).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env and environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    DEBUG: bool = False
    SECRET_KEY: str
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    # JWT
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # OAuth (Google)
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=5)
    RATE_LIMIT_WINDOW: int = Field(default=60)

    # Image Upload
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_IMAGE_SIZE: int = Field(default=5 * 1024 * 1024)  # 5 MB
    MAX_IMAGE_DIMENSION: int = Field(default=1200)

    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    FRONTEND_URL: str = Field(default="http://localhost:4200")

    # Email
    EMAIL_MODE: str = Field(default="log")  # "log" | "smtp"
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    EMAIL_FROM: str = Field(default="noreply@latiendita.local")


settings = Settings()
