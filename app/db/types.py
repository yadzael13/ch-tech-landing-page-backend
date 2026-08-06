import uuid
from datetime import UTC, datetime

from sqlalchemy import CHAR
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """DATETIME(6) that round-trips timezone-aware UTC datetimes.

    Two Postgres timestamptz behaviors this restores, neither of which a
    bare DATETIME column gives you on MySQL:

    1. fsp=6 (microsecond precision): MySQL's DATETIME defaults to fsp=0
       (whole seconds only), unlike Postgres's timestamp, which is
       microsecond-precision by default. Without this, every stored
       timestamp silently rounds to the nearest second.
    2. Timezone-awareness: MySQL's DATETIME has no timezone concept at all,
       so the DBAPI always returns naive datetimes — unlike asyncpg, which
       returns timezone-aware ones for timestamptz. Comparing a naive
       DB-read value against an aware `datetime.now(UTC)` elsewhere in the
       app (e.g. RefreshToken.is_active()) would silently return the wrong
       answer or raise TypeError. Every value the app writes is already
       normalized to UTC (app.db.base.utcnow) before it reaches this type,
       so it's safe to attach/strip UTC tzinfo mechanically here.
    """

    impl = DATETIME(fsp=6)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class GUID(TypeDecorator):
    """Portable UUID column: stores a canonical CHAR(36) string, returns uuid.UUID.

    MySQL has no native UUID type (unlike the Postgres UUID this replaces).
    CHAR(36) is chosen over BINARY(16) for readability/debuggability — this
    project's data volume (a landing page's content tables) doesn't justify
    the extra storage optimization. UUIDs are still generated client-side in
    Python (uuid.uuid4()), so generation logic is unaffected by this swap.
    """

    impl = CHAR(36)
    cache_ok = True

    @property
    def python_type(self) -> type[uuid.UUID]:
        return uuid.UUID

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value: str | None, dialect: object) -> uuid.UUID | None:
        if value is None:
            return None
        return uuid.UUID(value)
