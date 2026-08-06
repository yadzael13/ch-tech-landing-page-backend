"""ContactRequest entity (DATA_MODEL.md).

interested_service_line_id and source are optional additions from
CH-TECH V2 — the original POST /contact contract (name/email/company/
subject/message) remains valid without them.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import ContactStatus
from app.domain.value_objects import Email


@dataclass(slots=True)
class ContactRequest:
    id: uuid.UUID
    name: str
    email: Email
    company: str | None
    subject: str | None
    message: str
    interested_service_line_id: uuid.UUID | None
    source: str | None
    status: ContactStatus
    created_at: datetime
