"""Application settings loaded from environment variables."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for groceriesdeals."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5438
    postgres_db: str = "groceriesdeals"
    postgres_user: str = "groceriesdeals"
    postgres_password: str = "groceriesdeals"
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")
    anonymous_key_secret: str = Field(validation_alias="ANONYMOUS_KEY_SECRET")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Return the SQLAlchemy database URL."""
        if self.database_url_override:
            return self.database_url_override

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
