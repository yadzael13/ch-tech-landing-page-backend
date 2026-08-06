"""Testimonial entity (DATA_MODEL.md) — a client quote about CH-TECH's work."""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Testimonial:
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
