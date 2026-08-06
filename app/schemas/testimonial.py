import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TestimonialItem(BaseModel):
    id: uuid.UUID
    author_name: str
    author_role: str | None
    client_id: uuid.UUID | None
    project_id: uuid.UUID | None
    content: str
    rating: int | None
    featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestimonialWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT). client_id/project_id
    are optional but, when supplied, must reference an existing row (Fase 6
    use cases, same reasoning as CaseStudyWrite.project_id)."""

    author_name: str = Field(max_length=150)
    author_role: str | None = Field(default=None, max_length=150)
    client_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    content: str = Field(max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)
    featured: bool = False
