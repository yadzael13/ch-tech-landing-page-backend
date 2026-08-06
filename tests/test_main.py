from httpx import ASGITransport, AsyncClient

from app.main import app


def test_app_title() -> None:
    assert app.title == "CH-TECH API"


async def test_app_serves_requests() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
