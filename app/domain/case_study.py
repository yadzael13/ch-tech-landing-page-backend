"""CaseStudy entity (DATA_MODEL.md).

created_at/updated_at were missing from this entity in Fase 2, same gap as
app.domain.technology/service — fixed here in Fase 4 when CaseStudyItem
(API.md) needed them.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class CaseStudy:
    id: uuid.UUID
    project_id: uuid.UUID
    challenge: str | None
    solution: str | None
    architecture: str | None
    lessons_learned: str | None
    metrics: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
