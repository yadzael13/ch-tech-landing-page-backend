import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects import Image


class ServiceLineItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    icon: str | None
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceLineWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT)."""

    slug: str = Field(max_length=150)
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    icon: str | None = None
    display_order: int = 0

    @field_validator("icon")
    @classmethod
    def _validate_icon_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value
