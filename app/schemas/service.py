import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ServiceItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    featured: bool
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT). Field lengths mirror
    the DATABASE_SCHEMA.md column definitions (title VARCHAR(255), slug
    VARCHAR(150))."""

    slug: str = Field(max_length=150)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    featured: bool = False
    active: bool = True
