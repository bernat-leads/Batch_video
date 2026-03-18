"""Application settings — all config from environment variables."""

from typing import Literal

from pydantic import (
    AliasChoices,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables with API_ prefix."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="API_",
    )

    # ─── API ─────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "API"
    SECRET_KEY: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ─── Auth ──────────────────────────────────────────────────────────────
    APP_PASSWORD: str
    SESSION_MAX_AGE: int = 86400 * 7  # 7 days
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/api"
    )

    # ─── Server ──────────────────────────────────────────────────────────────
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "API_SERVER_PORT"),
    )
    SERVER_LOG_LEVEL: str = "info"
    SWAGGER_HIDE: bool = False

    # ─── Object Storage (S3-compatible) ──────────────────────────────────────
    S3_ENDPOINT: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "us-east-1"

    # ─── API Keys ─────────────────────────────────────────────────────────
    ELEVENLABS_API_KEY: str
    ANTHROPIC_API_KEY: str
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str

    # ─── Fonts ───────────────────────────────────────────────────────────
    FONT_DIR: str = "fonts"

    # ─── Pipeline ─────────────────────────────────────────────────────────
    PIPELINE_MAX_RETRIES: int = 5
    PIPELINE_RETRY_WAIT_SECONDS: int = 2

    # ─── Rate Limits (per provider, requests per minute, 0 = unlimited) ─
    GEMINI_RATE_LIMIT: int = 10
    OPENAI_RATE_LIMIT: int = 0
    ELEVENLABS_RATE_LIMIT: int = 12  # ~1 request every 5 seconds

    # ─── File uploads ─────────────────────────────────────────────────────
    UPLOAD_ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xls", ".csv"]
    UPLOAD_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # ─── Celery ───────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500

    # ─── Observability ────────────────────────────────────────────────────
    SENTRY_DSN: HttpUrl | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)

    # ─── Computed ─────────────────────────────────────────────────────────

    @computed_field
    @property
    def docs_url(self) -> str | None:
        """Swagger docs URL — hidden in non-local environments."""
        return None if self.SWAGGER_HIDE else "/docs"

    @computed_field
    @property
    def openapi_url(self) -> str | None:
        """OpenAPI spec URL — hidden in non-local environments."""
        return None if self.SWAGGER_HIDE else "/openapi.json"

    @computed_field
    @property
    def SERVER_APP_RELOAD(self) -> bool:
        """Auto-reload — only in local environment."""
        return self.ENVIRONMENT == "local"


settings = Settings()
