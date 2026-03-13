"""Shared database models (SQLAlchemy)."""

from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    """SQLAlchemy declarative base for all models (default public schema)."""
