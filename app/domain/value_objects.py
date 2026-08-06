"""Domain value objects (DATA_MODEL.md).

Pure Python, no framework dependencies (ARCHITECTURE.md dependency rule):
each value object validates its own invariant on construction and is
immutable once created.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URL_SCHEMES = {"http", "https"}
_PASSWORD_MIN_LENGTH = 8
# Well past any legitimate http(s) URL (browsers/servers cap around 2000-8000);
# without this, Url/Image accepted strings of unbounded length (OWASP
# API4:2023 — every field reusing these two value objects across the app
# inherits the cap for free).
_MAX_URL_LENGTH = 2048


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        # Normalize before validating: without this, "Admin@X" and "admin@x"
        # round-trip as distinct values through users.email's UNIQUE
        # constraint (case-sensitive by default Postgres collation), and
        # login becomes accidentally case-sensitive too.
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.fullmatch(normalized):
            raise ValueError(f"Invalid email address: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Slug:
    value: str

    def __post_init__(self) -> None:
        if not _SLUG_RE.fullmatch(self.value):
            raise ValueError(f"Invalid slug: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Url:
    value: str

    def __post_init__(self) -> None:
        if not _is_http_url(self.value):
            raise ValueError(f"Invalid URL: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Image:
    """A URL pointing to an image (DATA_MODEL.md — cover_image, logo, photo, icon)."""

    value: str

    def __post_init__(self) -> None:
        if not _is_http_url(self.value):
            raise ValueError(f"Invalid URL: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Password:
    """A plaintext password candidate, before hashing.

    Hashing is an infrastructure concern (see app.core.security) — this
    value object only enforces the domain's minimum length policy.
    """

    value: str

    def __post_init__(self) -> None:
        if len(self.value.strip()) < _PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {_PASSWORD_MIN_LENGTH} characters"
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MarkdownContent:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("MarkdownContent must not be blank")

    def __str__(self) -> str:
        return self.value


def _is_http_url(value: str) -> bool:
    if len(value) > _MAX_URL_LENGTH:
        return False
    parts = urlsplit(value)
    return parts.scheme in _URL_SCHEMES and bool(parts.netloc)
