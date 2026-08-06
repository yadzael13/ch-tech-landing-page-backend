from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.associations import article_technologies, project_technologies

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.project import Project


class Technology(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A technology used in projects and articles (DATABASE_SCHEMA.md)."""

    __tablename__ = "technologies"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    projects: Mapped[list["Project"]] = relationship(
        secondary=project_technologies, back_populates="technologies"
    )
    articles: Mapped[list["Article"]] = relationship(
        secondary=article_technologies, back_populates="technologies"
    )
