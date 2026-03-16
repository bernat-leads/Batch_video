import logging
from pathlib import Path
from typing import Literal

from pydantic import (
    AliasChoices,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

_settings_logger = logging.getLogger(__name__)


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
    SECRET_KEY: str = ""
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ─── Auth ──────────────────────────────────────────────────────────────
    APP_PASSWORD: str = Field(default="", min_length=1)
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

    # ─── OpenAI ──────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_TTS_MODEL: str = "gpt-4o-mini-tts"
    OPENAI_TTS_DEFAULT_VOICE: str = "coral"

    # ─── Pipeline ─────────────────────────────────────────────────────────
    ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    PIPELINE_MAX_RETRIES: int = 3
    PIPELINE_RETRY_WAIT_SECONDS: int = 2

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

    # ─── Celery task limits ─────────────────────────────────────────────────
    CELERY_TASK_TIME_LIMIT: int = 1800  # 30 minutes hard kill
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500  # 25 minutes soft warning

    # ─── Assembly font ──────────────────────────────────────────────────────
    CAPTION_FONT_PATH: str = ""

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Ensure required secrets are set in non-local environments."""
        if self.ENVIRONMENT == "local":
            return self

        required = {
            "SECRET_KEY": self.SECRET_KEY,
            "R2_ACCESS_KEY_ID": self.R2_ACCESS_KEY_ID,
            "R2_SECRET_ACCESS_KEY": self.R2_SECRET_ACCESS_KEY,
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            msg = (
                f"Required secrets not set for {self.ENVIRONMENT}: {', '.join(missing)}"
            )
            raise ValueError(msg)

        if len(self.APP_PASSWORD) < 8:
            msg = "APP_PASSWORD must be at least 8 characters in non-local environments"
            raise ValueError(msg)

        if "*" in self.CORS_ORIGINS:
            _settings_logger.warning(
                "CORS_ORIGINS contains '*' in %s environment — restrict to specific origins",
                self.ENVIRONMENT,
            )

        return self

    @model_validator(mode="after")
    def _set_default_font_path(self) -> "Settings":
        """Default to the bundled Montserrat-Bold.ttf font."""
        if not self.CAPTION_FONT_PATH:
            bundled = (
                Path(__file__).resolve().parent.parent / "fonts" / "Montserrat-Bold.ttf"
            )
            self.CAPTION_FONT_PATH = str(bundled)
        return self


settings = Settings()
