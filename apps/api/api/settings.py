import secrets
from typing import Any, Literal

from pydantic import (
    AliasChoices,
    Field,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="API_",  # Env vars: API_DATABASE_URL, API_OPENAI_API_KEY, etc.
    )

    # ─── API ─────────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "API"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # ─── Database ────────────────────────────────────────────────────────────
    # API uses its own Postgres database (separate from the Next.js app DB).
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

    # ─── OAuth / Better Auth ─────────────────────────────────────────────────
    OAUTH_PROVIDER_BASE_URL: str = "http://localhost:3002"
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""

    OAUTH_ISSUER_URL: str = ""
    OAUTH_AUDIENCE: str = ""

    @model_validator(mode="after")
    def _default_oauth_fields(self) -> "Settings":
        if not self.OAUTH_ISSUER_URL:
            self.OAUTH_ISSUER_URL = self.OAUTH_PROVIDER_BASE_URL
        if not self.OAUTH_AUDIENCE:
            self.OAUTH_AUDIENCE = self.OAUTH_PROVIDER_BASE_URL
        return self

    @computed_field
    @property
    def OAUTH_PROVIDER_JWKS_URL(self) -> str:
        return f"{self.OAUTH_PROVIDER_BASE_URL.rstrip('/')}/api/auth/jwks"

    @computed_field
    @property
    def OAUTH_PROVIDER_URL(self) -> str:
        return f"{self.OAUTH_PROVIDER_BASE_URL.rstrip('/')}/api/auth/oauth2"

    @computed_field
    @property
    def OAUTH_PROVIDER_USERINFO_URL(self) -> str:
        return f"{self.OAUTH_PROVIDER_BASE_URL.rstrip('/')}/api/auth/oauth2/userinfo"

    # ─── OpenAI ──────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ─── Apify ───────────────────────────────────────────────────────────────
    APIFY_API_TOKEN: str = ""

    # ─── Tavily ─────────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = ""

    # ─── File uploads ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"

    # ─── Langfuse ──────────────────────────────────────────────────────────
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

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
    def swagger_ui_init_oauth(self) -> dict[str, Any] | None:
        if self.SWAGGER_HIDE or not self.OAUTH_CLIENT_ID:
            return None
        return {
            "clientId": self.OAUTH_CLIENT_ID,
            "appName": f"{self.PROJECT_NAME} Docs",
            "usePkceWithAuthorizationCodeGrant": True,
            "scopes": "openid profile email",
        }

    @computed_field
    @property
    def SERVER_APP_RELOAD(self) -> bool:
        """Disable reload in non-local environments."""
        return self.ENVIRONMENT == "local"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"


settings = Settings()
