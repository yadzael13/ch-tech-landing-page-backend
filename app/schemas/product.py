import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import ProductStatus
from app.domain.value_objects import Image, Url


class ProductItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    short_description: str | None
    full_description: str | None
    status: str
    url: str | None
    logo: str | None
    featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT) — API.md validation
    rules: name required, slug unique, status required."""

    slug: str = Field(max_length=150)
    name: str = Field(max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = Field(default=None, max_length=20_000)
    status: ProductStatus = ProductStatus.WAITLIST
    url: str | None = None
    logo: str | None = None
    featured: bool = False

    @field_validator("url")
    @classmethod
    def _validate_url_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Url(value)
        return value

    @field_validator("logo")
    @classmethod
    def _validate_logo_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value
