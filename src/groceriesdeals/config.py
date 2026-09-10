"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for groceriesdeals."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anonymous_key_secret: str = Field(validation_alias="ANONYMOUS_KEY_SECRET")
    posthog_project_token: str = Field(validation_alias="POSTHOG_PROJECT_TOKEN")
    posthog_host: HttpUrl = Field(validation_alias="POSTHOG_HOST")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
