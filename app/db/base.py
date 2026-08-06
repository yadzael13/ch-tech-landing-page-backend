import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.types import GUID, UTCDateTime


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    """Every table uses a UUID primary key (DATABASE_SCHEMA.md)."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Every table records created_at/updated_at in UTC (DATABASE_SCHEMA.md)."""

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
