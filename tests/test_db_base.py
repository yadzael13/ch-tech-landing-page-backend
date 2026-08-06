import uuid

from sqlalchemy import String, inspect
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class _Widget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "_widgets_test_only"

    # Explicit length: unlike Postgres, MySQL's VARCHAR requires one — a
    # bare mapped_column() here previously compiled fine under Postgres but
    # raised sqlalchemy.exc.CompileError on every db_session-based test for
    # the rest of the pytest session once this module was collected (this
    # table is registered on the shared Base.metadata at import time).
    name: Mapped[str] = mapped_column(String(255))


def test_uuid_primary_key_mixin_defines_uuid_primary_key() -> None:
    mapper = inspect(_Widget)

    pk_columns = [column.name for column in mapper.primary_key]

    assert pk_columns == ["id"]
    assert mapper.columns["id"].type.python_type is uuid.UUID


def test_timestamp_mixin_defines_required_audit_columns() -> None:
    mapper = inspect(_Widget)

    assert mapper.columns["created_at"].nullable is False
    assert mapper.columns["updated_at"].nullable is False
