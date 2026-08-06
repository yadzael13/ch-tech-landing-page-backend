import uuid
from typing import Any

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class CaseStudy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The technical write-up of a project (DATABASE_SCHEMA.md)."""

    __tablename__ = "case_studies"

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id"), nullable=False
    )
    challenge: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    architecture: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    # MySQL JSON (native since 5.7.8) replaces Postgres JSONB — no JSONB
    # operators (@>, ?, jsonb_path_ops) are used in app code, so this is a
    # straightforward type swap.
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
