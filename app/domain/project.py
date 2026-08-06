"""Project entity (DATA_MODEL.md).

client_id is optional: a project is CH-TECH's own work (SaaS, Open Source,
Personal, Experimental) unless it references a client (CH-TECH V2).
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import ProjectStatus, Visibility
from app.domain.value_objects import Image, Slug, Url


@dataclass(slots=True)
class Project:
    id: uuid.UUID
    slug: Slug
    title: str
    short_description: str | None
    full_description: str | None
    repository_url: Url | None
    live_demo_url: Url | None
    cover_image: Image | None
    status: ProjectStatus
    visibility: Visibility
    featured: bool
    client_id: uuid.UUID | None
    started_at: date | None
    finished_at: date | None
    created_at: datetime
    updated_at: datetime
