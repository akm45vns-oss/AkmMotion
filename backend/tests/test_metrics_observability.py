import pytest
import re
from uuid import uuid4
from httpx import AsyncClient
from app.core.metrics import (
    record_http_request,
    sanitize_metrics_path,
    render_prometheus_metrics,
    HTTP_REQUESTS_TOTAL,
    RENDER_JOBS_TOTAL,
    QUOTA_OPERATIONS_TOTAL
)


@pytest.mark.asyncio
async def test_metrics_endpoint_scraped_successfully(client: AsyncClient):
    """Verifies that GET /metrics returns standard Prometheus formatted metric text."""
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    body = res.text

    # Verify our custom metrics are registered and scraped
    assert "akmmotion_http_requests_total" in body
    assert "akmmotion_http_request_duration_seconds" in body
    assert "akmmotion_active_requests" in body
    assert "akmmotion_render_jobs_total" in body
    assert "akmmotion_quota_operations_total" in body


@pytest.mark.asyncio
async def test_metrics_path_sanitization_prevents_high_cardinality():
    """Verifies that dynamic IDs and UUIDs are collapsed to prevent metric memory leaks."""
    raw_path_uuid = f"/api/v1/projects/{uuid4()}"
    clean = sanitize_metrics_path(raw_path_uuid)
    assert clean == "/api/v1/projects/{id}"

    raw_hex_path = f"/api/v1/workspaces/organizations/{uuid4().hex}"
    clean_hex = sanitize_metrics_path(raw_hex_path)
    assert clean_hex == "/api/v1/workspaces/organizations/{id}"

    static_path = "/health/ready"
    assert sanitize_metrics_path(static_path) == "/health/ready"


@pytest.mark.asyncio
async def test_http_request_metrics_incremented(client: AsyncClient):
    """Verifies that incoming HTTP requests properly record metrics in Prometheus."""
    # Hit health endpoint
    res = await client.get("/health/live")
    assert res.status_code == 200

    # Scrape metrics
    metrics_res = await client.get("/metrics")
    assert metrics_res.status_code == 200
    metrics_text = metrics_res.text

    # Must contain label with /health/live and status 200
    pattern = r'akmmotion_http_requests_total\{[^}]*path="/health/live"[^}]*status_code="200"[^}]*\}'
    assert re.search(pattern, metrics_text) is not None


@pytest.mark.asyncio
async def test_request_id_correlation_propagation(client: AsyncClient):
    """
    Verifies that X-Request-ID is propagated end-to-end:
    1. If client sends X-Request-ID, response returns exact same ID.
    2. If client does not send X-Request-ID, server generates a valid UUID and returns it.
    """
    custom_trace_id = f"trace-{uuid4().hex}"
    res_custom = await client.get("/health/live", headers={"X-Request-ID": custom_trace_id})
    assert res_custom.status_code == 200
    assert res_custom.headers.get("X-Request-ID") == custom_trace_id

    # Automatic generation
    res_auto = await client.get("/health/live")
    assert res_auto.status_code == 200
    auto_id = res_auto.headers.get("X-Request-ID")
    assert auto_id is not None
    # Verify valid UUID format
    assert len(auto_id) == 36
    assert auto_id.count("-") == 4
