from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ServiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One of CH-TECH's five business lines (DATABASE_SCHEMA.md, VISION.md)."""

    __tablename__ = "service_lines"

    slug: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
