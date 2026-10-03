import pytest
from unittest.mock import patch, MagicMock
from app.services.ai.providers.base import ProviderState
from app.services.ai.providers.fal_provider import FalProvider
from app.services.ai.providers.fallback_provider import FallbackProvider
from app.services.ai.providers.provider_manager import ProviderManager


@pytest.mark.asyncio
async def test_provider_health_summary():
    manager = ProviderManager()
    summary = manager.get_health_summary()
    assert "fal.ai" in summary
    assert "fallback_ken_burns" in summary
    assert summary["fallback_ken_burns"] == "HEALTHY"


@pytest.mark.asyncio
async def test_fal_quota_exhaustion_routes_to_fallback():
    manager = ProviderManager()
    fal_provider = manager.fal

    # Initially healthy
    assert fal_provider.state in [ProviderState.HEALTHY, ProviderState.DISABLED]

    # Simulate 403 quota lock
    fal_provider.record_failure(status_code=403)
    assert fal_provider.state == ProviderState.DEGRADED

    # Provider manager should automatically select fallback provider
    selected_provider = manager.get_provider()
    assert selected_provider.name == "fallback_ken_burns"
    assert selected_provider.state == ProviderState.HEALTHY


@pytest.mark.asyncio
async def test_fallback_provider_job_execution():
    fallback = FallbackProvider()
    res = await fallback.submit_job(
        prompt="A smiling person outdoors",
        aspect_ratio="9:16",
        image_url="https://example.com/asset.jpg"
    )
    assert res["status"] == "COMPLETED"
    assert res["provider"] == "fallback_ken_burns"
    assert res["video_url"] == "https://example.com/asset.jpg"

    status_res = await fallback.poll_job(res["request_id"])
    assert status_res["status"] == "COMPLETED"
