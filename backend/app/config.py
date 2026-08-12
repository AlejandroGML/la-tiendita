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
    GOOGLE_OAUTH_REDIRECT_URI: str = Field(default="http://localhost:4200/auth/google/callback")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=20)
    RATE_LIMIT_WINDOW: int = Field(default=60)

    # Image Upload
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_IMAGE_SIZE: int = Field(default=5 * 1024 * 1024)  # 5 MB
    MAX_IMAGE_DIMENSION: int = Field(default=1200)

    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    # Swish — mock por defecto (sin certificados ni cuenta de comerciante)
    SWISH_MODE: str = Field(default="mock")  # "mock" | "live"
    SWISH_PAYEE_ALIAS: str = Field(default="1234567890")
    FRONTEND_URL: str = Field(default="http://localhost:4200")

    # Email
    EMAIL_MODE: str = Field(default="log")  # "log" | "smtp" | "resend"
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    RESEND_API_KEY: str = Field(default="")
    EMAIL_FROM: str = Field(default="noreply@latiendita.local")

    # Frontend SPA — served by the backend in single-container deployments
    FRONTEND_DIST_DIR: str = Field(default="")

    # Redis cache
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_PREFIX: str = Field(default="tiendita")
    CACHE_TTL_PRODUCTS_LIST: int = Field(default=60)
    CACHE_TTL_PRODUCT_DETAIL: int = Field(default=300)
    CACHE_TTL_CATEGORIES_LIST: int = Field(default=600)
    CACHE_TTL_PROMOTIONS_ACTIVE: int = Field(default=120)

    # ARQ background jobs
    ARQ_QUEUE_NAME: str = Field(default="arq:queue")

    # Sentry error tracking (optional — leave empty to disable)
    SENTRY_DSN: str = Field(default="")


settings = Settings()
