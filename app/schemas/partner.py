import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects import Image, Url


class PartnerItem(BaseModel):
    id: uuid.UUID
    name: str
    logo: str | None
    partnership_type: str | None
    website_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT)."""

    name: str = Field(max_length=255)
    logo: str | None = None
    partnership_type: str | None = Field(default=None, max_length=100)
    website_url: str | None = None

    @field_validator("logo")
    @classmethod
    def _validate_logo_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value

    @field_validator("website_url")
    @classmethod
    def _validate_website_url_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Url(value)
        return value
