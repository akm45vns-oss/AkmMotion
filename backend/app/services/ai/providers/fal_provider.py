import time
import logging
from typing import Dict, Any, Optional

from app.services.ai.providers.base import VideoGenerationProvider, ProviderState
from app.services.ai.fal_video_service import FalVideoService
from app.core.config import settings

logger = logging.getLogger(__name__)


class FalProvider(VideoGenerationProvider):
    """
    fal.ai Kling / LTX video generation provider with dynamic health tracking.
    """

    def __init__(self):
        self.service = FalVideoService()
        self._state = ProviderState.HEALTHY
        self._consecutive_failures = 0
        self._last_error_time = 0.0

    @property
    def name(self) -> str:
        return "fal.ai"

    @property
    def state(self) -> ProviderState:
        if not settings.FAL_VIDEO_ENABLED or not self.service.api_key:
            return ProviderState.DISABLED
        # Recovery window: after 5 minutes, attempt self-healing from DEGRADED
        if self._state == ProviderState.DEGRADED and (time.time() - self._last_error_time) > 300:
            self._state = ProviderState.HEALTHY
            self._consecutive_failures = 0
        return self._state

    def record_success(self):
        self._consecutive_failures = 0
        self._state = ProviderState.HEALTHY

    def record_failure(self, status_code: int = 500):
        self._consecutive_failures += 1
        self._last_error_time = time.time()
        # If 403 (quota lock/balance exhaustion), immediately mark DEGRADED
        if status_code in [402, 403]:
            self._state = ProviderState.DEGRADED
            logger.warning("[FalProvider] fal.ai returned billing/quota exhaustion (403). State set to DEGRADED.")
        elif self._consecutive_failures >= 3:
            self._state = ProviderState.DEGRADED

    async def submit_job(self, prompt: str, aspect_ratio: str = "9:16", image_url: Optional[str] = None) -> Dict[str, Any]:
        try:
            result = await self.service.submit_text_to_video(prompt, aspect_ratio=aspect_ratio)
            self.record_success()
            return {
                "request_id": result.get("request_id"),
                "status": result.get("status", "IN_QUEUE"),
                "provider": self.name
            }
        except Exception as exc:
            status_code = getattr(exc, "status_code", 500)
            self.record_failure(status_code)
            raise exc

    async def poll_job(self, provider_request_id: str) -> Dict[str, Any]:
        return await self.service.check_status(provider_request_id)

    async def fetch_result(self, provider_request_id: str) -> Dict[str, Any]:
        return await self.service.fetch_result(provider_request_id)
