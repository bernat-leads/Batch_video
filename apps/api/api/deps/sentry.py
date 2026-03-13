"""Sentry SDK initialization and configuration."""

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from api.settings import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry SDK if DSN is configured."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping initialization")
        return

    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
        send_default_pii=False,
    )
    logger.info("Sentry initialized for environment: %s", settings.ENVIRONMENT)
