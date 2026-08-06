import json
import logging
import sys
from types import TracebackType

from app.core.logging_config import JSONFormatter, configure_logging

_ExcInfo = (
    tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
)


def _make_record(
    level: int = logging.INFO,
    message: str = "hello",
    exc_info: _ExcInfo | None = None,
) -> logging.LogRecord:
    return logging.LogRecord(
        name="app.test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=exc_info,
    )


def test_json_formatter_produces_valid_json_with_expected_fields() -> None:
    formatter = JSONFormatter()
    record = _make_record(message="hello world")

    output = json.loads(formatter.format(record))

    assert output["level"] == "INFO"
    assert output["logger"] == "app.test"
    assert output["message"] == "hello world"
    assert "timestamp" in output


def test_json_formatter_includes_exception_info() -> None:
    formatter = JSONFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        record = _make_record(level=logging.ERROR, exc_info=sys.exc_info())

    output = json.loads(formatter.format(record))

    assert "ValueError: boom" in output["exception"]


def test_configure_logging_attaches_a_json_formatter_to_the_root_logger() -> None:
    configure_logging()

    root = logging.getLogger()

    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JSONFormatter)
