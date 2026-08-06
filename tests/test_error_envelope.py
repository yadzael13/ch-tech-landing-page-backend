from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_unmatched_route_returns_error_envelope() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body == {
        "success": False,
        "error": {"code": "RESOURCE_NOT_FOUND", "message": "Not Found"},
    }
