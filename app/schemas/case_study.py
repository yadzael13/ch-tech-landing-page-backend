import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CaseStudyItem(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    challenge: str | None
    solution: str | None
    architecture: str | None
    lessons_learned: str | None
    metrics: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseStudyWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT)."""

    project_id: uuid.UUID
    challenge: str | None = Field(default=None, max_length=10_000)
    solution: str | None = Field(default=None, max_length=10_000)
    architecture: str | None = Field(default=None, max_length=10_000)
    lessons_learned: str | None = Field(default=None, max_length=10_000)
    metrics: dict[str, Any] | None = None
