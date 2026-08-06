"""TeamMember entity (DATA_MODEL.md).

user_id is optional: not every team member has admin panel access.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, Url


@dataclass(slots=True)
class TeamMember:
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    role: str
    bio: str | None
    photo: Image | None
    linkedin_url: Url | None
    github_url: Url | None
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime
