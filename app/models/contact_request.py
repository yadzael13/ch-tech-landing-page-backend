import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, utcnow
from app.db.types import GUID, UTCDateTime


class ContactStatus(StrEnum):
    NEW = "NEW"
    READ = "READ"
    REPLIED = "REPLIED"
    ARCHIVED = "ARCHIVED"


class ContactRequest(Base, UUIDPrimaryKeyMixin):
    """A submission from the contact form (DATABASE_SCHEMA.md).

    Fire-and-forget: only created_at, no updated_at.
    """

    __tablename__ = "contact_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW', 'READ', 'REPLIED', 'ARCHIVED')",
            name="ck_contact_requests_status",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Both optional additions from CH-TECH V2 (DATA_MODEL.md) — the original
    # POST /contact contract remains valid without them.
    interested_service_line_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("service_lines.id"),
        nullable=True,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ContactStatus.NEW.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, nullable=False, index=True
    )
