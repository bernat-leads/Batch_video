"""Celery tasks for background processing."""

import logging

from api.deps.celery import celery_app  # noqa: F401

logger = logging.getLogger(__name__)
