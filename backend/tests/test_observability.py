import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    resp = await client.get("/health/ready")
    assert resp.status_code in [200, 503]
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "storage" in data["checks"]


@pytest.mark.asyncio
async def test_health_stats(client: AsyncClient):
    resp = await client.get("/health/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_global_renders" in data
    assert "storage" in data
    assert "providers" in data


@pytest.mark.asyncio
async def test_request_id_middleware(client: AsyncClient):
    # Test request ID generation
    resp = await client.get("/health/live")
    assert "x-request-id" in resp.headers
    generated_id = resp.headers["x-request-id"]
    assert len(generated_id) > 10

    # Test request ID preservation if provided by client
    custom_id = "test-client-req-999"
    resp2 = await client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert resp2.headers.get("x-request-id") == custom_id
