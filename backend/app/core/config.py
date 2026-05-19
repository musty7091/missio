from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="Missio", alias="MISSIO_APP_NAME")
    environment: str = Field(default="local", alias="MISSIO_ENVIRONMENT")
    debug: bool = Field(default=True, alias="MISSIO_DEBUG")
    default_timezone: str = Field(default="Europe/Istanbul", alias="MISSIO_DEFAULT_TIMEZONE")
    database_url: str = Field(default="sqlite:///./missio_local.db", alias="MISSIO_DATABASE_URL")
    secret_key: str = Field(
        default="change-this-secret-key-before-production",
        alias="MISSIO_SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        alias="MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES",
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
