"""Celery tasks for background processing."""

import logging

from worker.app import celery_app  # noqa: F401

logger = logging.getLogger(__name__)
