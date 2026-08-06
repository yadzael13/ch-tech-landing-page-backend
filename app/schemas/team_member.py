import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects import Image, Url


class TeamMemberItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    role: str
    bio: str | None
    photo: str | None
    linkedin_url: str | None
    github_url: str | None
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT). user_id is optional
    but, when supplied, must reference an existing user (Fase 6 use cases)."""

    user_id: uuid.UUID | None = None
    name: str = Field(max_length=150)
    role: str = Field(max_length=150)
    bio: str | None = Field(default=None, max_length=2000)
    photo: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    display_order: int = 0
    active: bool = True

    @field_validator("photo")
    @classmethod
    def _validate_photo_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value

    @field_validator("linkedin_url", "github_url")
    @classmethod
    def _validate_profile_url_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Url(value)
        return value
