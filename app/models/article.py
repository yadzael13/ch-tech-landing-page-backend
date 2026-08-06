import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID, UTCDateTime
from app.models.associations import article_technologies

if TYPE_CHECKING:
    from app.models.technology import Technology


class Article(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A technical publication (DATABASE_SCHEMA.md)."""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "NOT published OR published_at IS NOT NULL",
            name="ck_articles_published_requires_published_at",
        ),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    technologies: Mapped[list["Technology"]] = relationship(
        secondary=article_technologies, back_populates="articles"
    )
