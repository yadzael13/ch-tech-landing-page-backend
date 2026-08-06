from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, Computed, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import UTCDateTime


class UserRole(StrEnum):
    ADMIN = "ADMIN"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Administrator of the system (DATA_MODEL.md — no end-user accounts, ADR-0003)."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN')", name="ck_users_role"),
        # Defense in depth alongside email's plain UNIQUE below: the domain
        # Email value object normalizes to lowercase before it ever reaches
        # here, but this backstops any write path that bypasses it (e.g. a
        # raw model construction) from creating "Admin@x" and "admin@x" as
        # two distinct rows. MySQL doesn't support indexing an arbitrary
        # expression like Postgres does (the old
        # `Index(..., text("lower(email)"))`) — a persisted generated column
        # is the portable equivalent.
        Index("uq_users_email_lower", "email_lower", unique=True),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_lower: Mapped[str] = mapped_column(
        String(255), Computed("LOWER(email)", persisted=True), nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default=UserRole.ADMIN.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
