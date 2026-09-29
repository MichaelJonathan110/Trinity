"""Application settings. Values come from environment variables (.env);
no secret is ever hardcoded here (spec 58, 72)."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TRINITY"
    ENV: str = "development"
    API_V1: str = "/api/v1"

    # Security
    SECRET_KEY: str = "dev-only-change-me"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Data stores
    DATABASE_URL: str = "postgresql+psycopg://trinity:trinity@localhost:5432/trinity"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Where progress-photo files live. Never inside the repo's static bundle; the
    # file route re-checks ownership on every read (spec 59).
    MEDIA_ROOT: str = "media"

    # CORS - explicit origins only (spec 58)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalise_database_url(cls, value: str) -> str:
        """Accept the bare URLs managed hosts hand out.

        Render (and Heroku) give ``postgres://`` or ``postgresql://``, which
        SQLAlchemy maps to the psycopg2 driver. We ship psycopg3
        (``psycopg[binary]``), so rewrite the scheme to
        ``postgresql+psycopg://``. Idempotent: a URL that already carries the
        driver is returned untouched.
        """
        for bare in ("postgres://", "postgresql://"):
            if value.startswith(bare):
                return "postgresql+psycopg://" + value[len(bare):]
        return value

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
