from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Partner(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A technology or business alliance of CH-TECH (DATABASE_SCHEMA.md)."""

    __tablename__ = "partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    partnership_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
