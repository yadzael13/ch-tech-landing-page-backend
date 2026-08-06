import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A professional service offered (DATABASE_SCHEMA.md)."""

    __tablename__ = "services"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # DATA_MODEL.md documents this as required once an admin UI exists to
    # assign it (CH-TECH V2). Nullable for now, same reasoning as
    # projects.client_id: enforcing NOT NULL today would mean inventing a
    # backfill value with no real basis. Tightened in a later migration
    # once Fase 6 (ServiceLine CRUD) lands.
    service_line_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("service_lines.id"), nullable=True, index=True
    )
