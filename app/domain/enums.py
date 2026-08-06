"""Domain enums (DATA_MODEL.md).

Mirrors the enums already defined alongside the SQLAlchemy models
(app.models.*) — duplicated here, not imported from there, because
app.models depends on SQLAlchemy and domain must not (ARCHITECTURE.md).
"""

from enum import StrEnum


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Visibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class ContactStatus(StrEnum):
    NEW = "NEW"
    READ = "READ"
    REPLIED = "REPLIED"
    ARCHIVED = "ARCHIVED"


class UserRole(StrEnum):
    ADMIN = "ADMIN"


class ProductStatus(StrEnum):
    WAITLIST = "WAITLIST"
    BETA = "BETA"
    LIVE = "LIVE"
