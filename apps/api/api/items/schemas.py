"""Item Pydantic schemas — example request/response models for the template."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ItemCreate(BaseModel):
    title: str
    content: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class ItemResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    title: str
    content: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
