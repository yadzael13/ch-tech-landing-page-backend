import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects import Image, Url


class TechnologyItem(BaseModel):
    """Shared shape for list and detail — Technology has no separate summary
    view since it carries no relations to expand or omit."""

    id: uuid.UUID
    name: str
    category: str | None
    icon: str | None
    official_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TechnologyWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT).

    Field lengths mirror the DATABASE_SCHEMA.md column definitions
    (name/category VARCHAR(100)) so oversized input fails fast with a 422
    instead of a DB-level error.
    """

    name: str = Field(max_length=100)
    category: str | None = Field(default=None, max_length=100)
    icon: str | None = None
    official_url: str | None = None

    @field_validator("icon")
    @classmethod
    def _validate_icon_shape(cls, value: str | None) -> str | None:
        # Reuses the domain Image value object (ADR-0012) — a ValueError
        # here becomes a standard 422 VALIDATION_ERROR (API.md).
        if value is not None:
            Image(value)
        return value

    @field_validator("official_url")
    @classmethod
    def _validate_official_url_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Url(value)
        return value
