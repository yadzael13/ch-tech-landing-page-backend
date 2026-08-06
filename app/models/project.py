import uuid
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID
from app.models.associations import project_technologies

if TYPE_CHECKING:
    from app.models.technology import Technology


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Visibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A project shown in the portfolio (DATABASE_SCHEMA.md)."""

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PLANNING', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "visibility IN ('PUBLIC', 'PRIVATE')", name="ck_projects_visibility"
        ),
    )

    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    # Indexed (plain B-tree) to back the title search in project_repository.py
    # — replaces the Postgres pg_trgm/GIN trigram index, which has no MySQL
    # equivalent and wasn't needed for a catalog this small anyway.
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    live_demo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProjectStatus.PLANNING.value, index=True
    )
    visibility: Mapped[str] = mapped_column(
        String(50), nullable=False, default=Visibility.PRIVATE.value
    )
    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    finished_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    # NULL for CH-TECH's own work (SaaS/Open Source/Personal/Experimental);
    # set for client projects (CH-TECH V2, DATA_MODEL.md).
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("clients.id"), nullable=True, index=True
    )

    technologies: Mapped[list["Technology"]] = relationship(
        secondary=project_technologies, back_populates="projects"
    )
