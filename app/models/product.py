from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductStatus(StrEnum):
    WAITLIST = "WAITLIST"
    BETA = "BETA"
    LIVE = "LIVE"


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A CH-TECH SaaS product in the public catalog (DATABASE_SCHEMA.md, ADR-0013).

    Catalog only — no tenants, plans, or billing (see ADR-0013).
    """

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "status IN ('WAITLIST', 'BETA', 'LIVE')", name="ck_products_status"
        ),
    )

    slug: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProductStatus.WAITLIST.value, index=True
    )
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
