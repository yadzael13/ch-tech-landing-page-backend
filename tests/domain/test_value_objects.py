import pytest

from app.domain.value_objects import Email, Image, MarkdownContent, Password, Slug, Url


def test_email_accepts_a_valid_address() -> None:
    assert str(Email("hello@ch-tech.dev")) == "hello@ch-tech.dev"


def test_email_normalizes_to_lowercase() -> None:
    assert str(Email("Hello@CH-TECH.dev")) == "hello@ch-tech.dev"


def test_email_strips_surrounding_whitespace() -> None:
    assert str(Email("  hello@ch-tech.dev  ")) == "hello@ch-tech.dev"


@pytest.mark.parametrize(
    "raw", ["", "not-an-email", "missing-domain@", "@missing-local.com"]
)
def test_email_rejects_invalid_addresses(raw: str) -> None:
    with pytest.raises(ValueError, match="email"):
        Email(raw)


def test_slug_accepts_lowercase_hyphenated_value() -> None:
    assert str(Slug("ch-tech-v2")) == "ch-tech-v2"


@pytest.mark.parametrize(
    "raw",
    ["", "Has-Upper", "has_underscore", "-leading", "trailing-", "double--hyphen"],
)
def test_slug_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(ValueError, match="slug"):
        Slug(raw)


def test_url_accepts_http_and_https() -> None:
    assert str(Url("https://ch-tech.dev")) == "https://ch-tech.dev"
    assert str(Url("http://localhost:8000")) == "http://localhost:8000"


@pytest.mark.parametrize(
    "raw", ["", "ftp://ch-tech.dev", "not-a-url", "javascript:alert(1)"]
)
def test_url_rejects_non_http_values(raw: str) -> None:
    with pytest.raises(ValueError, match="URL"):
        Url(raw)


def test_url_rejects_a_value_past_the_length_cap() -> None:
    oversized = "https://ch-tech.dev/" + "a" * 2048
    with pytest.raises(ValueError, match="URL"):
        Url(oversized)


def test_image_accepts_an_http_url() -> None:
    assert (
        str(Image("https://ch-tech.dev/cover.png")) == "https://ch-tech.dev/cover.png"
    )


def test_image_rejects_a_non_url_value() -> None:
    with pytest.raises(ValueError, match="URL"):
        Image("not-a-url")


def test_password_accepts_eight_characters_or_more() -> None:
    assert str(Password("correct-horse")) == "correct-horse"


@pytest.mark.parametrize("raw", ["", "short1", "       "])
def test_password_rejects_short_or_blank_values(raw: str) -> None:
    with pytest.raises(ValueError, match="Password"):
        Password(raw)


def test_markdown_content_accepts_non_blank_text() -> None:
    assert str(MarkdownContent("# Title\n\nBody")) == "# Title\n\nBody"


@pytest.mark.parametrize("raw", ["", "   ", "\n\n"])
def test_markdown_content_rejects_blank_text(raw: str) -> None:
    with pytest.raises(ValueError, match="MarkdownContent"):
        MarkdownContent(raw)


def test_value_objects_are_immutable() -> None:
    email = Email("hello@ch-tech.dev")
    with pytest.raises(AttributeError):
        email.value = "other@ch-tech.dev"  # type: ignore[misc]
