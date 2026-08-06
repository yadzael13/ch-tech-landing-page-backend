from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse[T](BaseModel):
    """The success envelope every endpoint response follows (API.md)."""

    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """The error envelope every error response follows (API.md)."""

    success: bool = False
    error: ErrorDetail
