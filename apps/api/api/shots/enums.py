"""Enums for shot status fields."""

import enum


class ShotStatus(str, enum.Enum):
    """Status of a shot in the image generation pipeline."""

    pending = "pending"
    generating = "generating"
    generated = "generated"
    failed = "failed"
