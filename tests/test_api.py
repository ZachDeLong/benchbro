import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from benchbro.app import create_app


@pytest.fixture
async def client(tmp_path):
    app = create_app(db_path=tmp_path / "test.db")
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


async def test_list_benchmarks(client):
    response = await client.get("/api/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    names = [item["name"] for item in data]
    assert "gsm8k" in names
    assert "mmlu_pro" in names


async def test_detect_backends(client):
    response = await client.get("/api/models/backends")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_list_sessions_empty(client):
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data == []
