from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The company's public profile (DATABASE_SCHEMA.md).

    Singleton: exactly one row. Enforced at the application layer (no
    POST/DELETE in API.md), not by a DB constraint.
    """

    __tablename__ = "companies"

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    # MySQL JSON (native since 5.7.8) replaces Postgres JSONB — see
    # case_study.py::metrics for the same reasoning.
    social_links: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
