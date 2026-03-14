import secrets
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="API_",  # Env vars: API_DATABASE_URL, API_R2_ACCOUNT_ID, etc.
    )

    # ─── API ─────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "API"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ─── Auth ──────────────────────────────────────────────────────────────
    APP_PASSWORD: str = ""
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
        validation_alias=AliasChoices("API_SERVER_PORT", "PORT"),
    )
    SERVER_LOG_LEVEL: str = "info"
    SWAGGER_HIDE: bool = False

    # ─── Cloudflare R2 ─────────────────────────────────────────────────────
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "video-pipeline"

    # ─── ElevenLabs ────────────────────────────────────────────────────────
    ELEVENLABS_API_KEY: str = ""

    # ─── Anthropic (Claude) ───────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""

    # ─── Google Gemini ─────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ─── File uploads ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    UPLOAD_ALLOWED_EXTENSIONS: list[str] = [".xlsx", ".xls", ".csv"]
    UPLOAD_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB


    # ─── Optional / Observability ────────────────────────────────────────────
    SENTRY_DSN: HttpUrl | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry performance traces sample rate (0.0 to 1.0)",
    )
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry profiling sample rate (0.0 to 1.0)",
    )

    @computed_field
    @property
    def docs_url(self) -> str | None:
        return None if self.SWAGGER_HIDE else "/docs"

    @computed_field
    @property
    def openapi_url(self) -> str | None:
        return None if self.SWAGGER_HIDE else "/openapi.json"

    @computed_field
    @property
    def SERVER_APP_RELOAD(self) -> bool:
        """Disable reload in non-local environments."""
        return self.ENVIRONMENT == "local"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"


settings = Settings()
