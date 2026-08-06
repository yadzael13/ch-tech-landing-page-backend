from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(title="CH-TECH API")

# Browser calls from the frontend (a different origin in dev: :3000 -> :8000)
# are blocked without this — not optional once a real frontend exists.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deliberately outside /api/v1: infra probes (uptime monitors, orchestrators)
# shouldn't have to track API version bumps to keep polling this.
app.include_router(health_router)
app.include_router(api_router)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
