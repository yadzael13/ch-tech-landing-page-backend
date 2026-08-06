import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Testimonial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A client quote about CH-TECH's work (DATABASE_SCHEMA.md)."""

    __tablename__ = "testimonials"
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5",
            name="ck_testimonials_rating_range",
        ),
    )

    author_name: Mapped[str] = mapped_column(String(150), nullable=False)
    author_role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("clients.id"), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("projects.id"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
