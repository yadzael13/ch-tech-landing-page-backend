class AppError(Exception):
    """A domain error carrying the machine-readable `code` API.md requires.

    Raise this (or a subclass) from endpoint/service code instead of the bare
    FastAPI HTTPException when the response needs a specific `error.code`.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class ResourceNotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(404, "RESOURCE_NOT_FOUND", message)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(409, "CONFLICT", message)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(401, "UNAUTHORIZED", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(403, "FORBIDDEN", message)
