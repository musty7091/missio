from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="Missio", alias="MISSIO_APP_NAME")
    environment: str = Field(default="local", alias="MISSIO_ENVIRONMENT")
    debug: bool = Field(default=True, alias="MISSIO_DEBUG")
    default_timezone: str = Field(
        default="Europe/Istanbul",
        alias="MISSIO_DEFAULT_TIMEZONE",
    )
    database_url: str = Field(
        default="sqlite:///./missio_local.db",
        alias="MISSIO_DATABASE_URL",
    )
    secret_key: str = Field(
        default="change-this-secret-key-before-production",
        alias="MISSIO_SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        alias="MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    cors_allowed_origins: str = Field(
        default="",
        alias="MISSIO_CORS_ALLOWED_ORIGINS",
    )

    web_push_enabled: bool = Field(
        default=False,
        alias="MISSIO_WEB_PUSH_ENABLED",
    )
    web_push_vapid_private_key_file: str = Field(
        default="",
        alias="MISSIO_WEB_PUSH_VAPID_PRIVATE_KEY_FILE",
    )
    web_push_vapid_public_key: str = Field(
        default="",
        alias="MISSIO_WEB_PUSH_VAPID_PUBLIC_KEY",
    )
    web_push_vapid_subject: str = Field(
        default="mailto:admin@example.com",
        alias="MISSIO_WEB_PUSH_VAPID_SUBJECT",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        alias="MISSIO_RATE_LIMIT_ENABLED",
    )
    rate_limit_max_requests: int = Field(
        default=120,
        alias="MISSIO_RATE_LIMIT_MAX_REQUESTS",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        alias="MISSIO_RATE_LIMIT_WINDOW_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
