from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


async def test_cors_allows_configured_frontend_origin() -> None:
    origin = get_settings().frontend_origin
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": origin})

    assert response.headers["access-control-allow-origin"] == origin


async def test_cors_rejects_unknown_origin() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health", headers={"Origin": "https://evil.example"}
        )

    assert "access-control-allow-origin" not in response.headers
