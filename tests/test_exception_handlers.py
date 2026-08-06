from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.errors import ConflictError, ResourceNotFoundError


def _build_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_exception_handler(ResourceNotFoundError, app_error_handler)
    test_app.add_exception_handler(ConflictError, app_error_handler)
    test_app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    test_app.add_exception_handler(Exception, unhandled_exception_handler)

    class Payload(BaseModel):
        name: str

    @test_app.get("/not-found")
    async def raise_not_found() -> None:
        raise ResourceNotFoundError("Project not found")

    @test_app.get("/conflict")
    async def raise_conflict() -> None:
        raise ConflictError("Slug already exists")

    @test_app.get("/boom")
    async def raise_unhandled() -> None:
        raise RuntimeError("something broke internally")

    @test_app.post("/validated")
    async def validated(payload: Payload) -> Payload:
        return payload

    return test_app


async def test_app_error_produces_its_own_code_and_message() -> None:
    transport = ASGITransport(app=_build_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {"code": "RESOURCE_NOT_FOUND", "message": "Project not found"},
    }


async def test_conflict_error_maps_to_409() -> None:
    transport = ASGITransport(app=_build_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_validation_error_returns_422_envelope() -> None:
    transport = ASGITransport(app=_build_test_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/validated", json={})

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {"code": "VALIDATION_ERROR", "message": "Invalid request data"},
    }


def test_unhandled_exception_returns_500_without_leaking_details() -> None:
    # ServerErrorMiddleware re-raises after sending the response (so the
    # exception still reaches server logs); only Starlette's TestClient knows
    # to swallow that re-raise once the response is captured — ASGITransport
    # would let it propagate straight into the test as a RuntimeError.
    client = TestClient(_build_test_app(), raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "something broke internally" not in body["error"]["message"]
