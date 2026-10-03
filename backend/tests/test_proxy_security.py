import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.core.rate_limit import _rate_limiter, extract_rate_limit_key
from fastapi import Request


@pytest.mark.asyncio
async def test_trusted_proxy_forwarded_for_respected(client: AsyncClient):
    """Verifies that reverse proxies in trusted_proxy_list have their X-Forwarded-For inspected."""
    _rate_limiter.reset()
    proxy_ip = "203.0.113.195"

    with patch("app.services.ai.script_analyzer.ScriptAnalyzerService.analyze_script", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = [{"scene_number": 1, "narration": "test"}]

        # From testclient (which is in trusted_proxy_list by default)
        for _ in range(21):
            await client.post(
                "/api/v1/ai/generate-scenes",
                json={"script": "Hello world", "language": "en"},
                headers={"X-Forwarded-For": proxy_ip}
            )

        # 21st request should be rate limited under that proxy IP
        res_blocked = await client.post(
            "/api/v1/ai/generate-scenes",
            json={"script": "Hello world", "language": "en"},
            headers={"X-Forwarded-For": proxy_ip}
        )
        assert res_blocked.status_code == 429


@pytest.mark.asyncio
async def test_untrusted_peer_forwarded_headers_ignored():
    """Verifies that an untrusted peer sending forged X-Forwarded-For cannot spoof IP."""
    class FakeClient:
        host = "198.51.100.99"  # Not in trusted_proxy_list

    class FakeRequest:
        client = FakeClient()
        headers = {"x-forwarded-for": "10.0.0.1", "cf-connecting-ip": "10.0.0.2"}
        cookies = {}

    key = extract_rate_limit_key(FakeRequest())
    # Must use actual client.host (198.51.100.99), NOT the forged headers
    assert key == "ip:198.51.100.99"


@pytest.mark.asyncio
async def test_spoofed_x_user_id_ignored_from_untrusted_peer():
    """A malicious client attempting to send X-User-ID: victim must have that header ignored."""
    class FakeClient:
        host = "203.0.113.50"  # Untrusted external IP

    class FakeRequest:
        client = FakeClient()
        headers = {"x-user-id": "victim-user-123"}
        cookies = {}

    key = extract_rate_limit_key(FakeRequest())
    # Header MUST be ignored and fallback to IP
    assert key == "ip:203.0.113.50"
    assert "victim-user-123" not in key
