import logging
from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError
from app.schemas.response import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

# Fallback mapping for status codes raised without a domain-specific AppError
# (e.g. framework-raised 404s for unmatched routes, or a bare HTTPException).
_STATUS_CODE_TO_ERROR_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
}


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


# Starlette's add_exception_handler() is keyed by exception class, so it only
# ever calls a given handler with the type it was registered for — but its
# own signature can't express that per-handler, hence `Exception` + cast()
# here instead of the narrower type mypy would otherwise want to (wrongly)
# reject at the registration call site.
async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(AppError, exc)
    return _error_response(error.status_code, error.code, error.message)


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exc)
    code = _STATUS_CODE_TO_ERROR_CODE.get(error.status_code, "HTTP_ERROR")
    return _error_response(error.status_code, code, str(error.detail))


async def validation_exception_handler(
    _request: Request, _exc: Exception
) -> JSONResponse:
    return _error_response(422, "VALIDATION_ERROR", "Invalid request data")


async def unhandled_exception_handler(
    request: Request, _exc: Exception
) -> JSONResponse:
    # Never leak internals (message, traceback) in the response — SECURITY.md.
    logger.exception("Unhandled exception while processing %s", request.url)
    return _error_response(500, "INTERNAL_SERVER_ERROR", "Internal server error")
