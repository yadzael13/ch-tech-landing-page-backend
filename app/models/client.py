from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Client(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A company or organization CH-TECH has worked with (DATABASE_SCHEMA.md)."""

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(150), nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
