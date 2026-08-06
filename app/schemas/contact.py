from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    """API.md - Validation Rules -> Contact: email must be valid, message
    between 20 and 5000 characters."""

    name: str = Field(max_length=255)
    email: EmailStr
    company: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=255)
    message: str = Field(min_length=20, max_length=5000)


class ContactReceived(BaseModel):
    """The exact (non-enveloped) shape API.md documents for POST /contact."""

    message: str = "Contact request received."
