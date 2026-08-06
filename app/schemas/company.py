import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class CompanyItem(BaseModel):
    id: uuid.UUID
    legal_name: str
    display_name: str
    tagline: str | None
    mission: str | None
    vision: str | None
    email: str | None
    phone: str | None
    address: str | None
    social_links: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyWrite(BaseModel):
    """PUT /admin/company — the only write endpoint (API.md): Company is a
    singleton with no POST/DELETE."""

    legal_name: str = Field(max_length=255)
    display_name: str = Field(max_length=150)
    tagline: str | None = Field(default=None, max_length=255)
    mission: str | None = Field(default=None, max_length=2000)
    vision: str | None = Field(default=None, max_length=2000)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    social_links: dict[str, Any] | None = None
