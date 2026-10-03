import enum
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ProviderState(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


class VideoGenerationProvider(ABC):
    """
    Abstract base class for all Text-to-Video and Scene-Animation providers.
    Ensures modular, vendor-agnostic architecture.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g. 'fal.ai', 'fallback_ken_burns')."""
        pass

    @property
    @abstractmethod
    def state(self) -> ProviderState:
        """Current operational health state."""
        pass

    @abstractmethod
    async def submit_job(self, prompt: str, aspect_ratio: str = "9:16", image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Submits video generation job.
        Returns dict with at least: {'job_id': str, 'status': str, 'provider': str}
        """
        pass

    @abstractmethod
    async def poll_job(self, provider_request_id: str) -> Dict[str, Any]:
        """
        Polls job progression.
        Returns dict with: {'status': str, 'progress': Optional[int]}
        """
        pass

    @abstractmethod
    async def fetch_result(self, provider_request_id: str) -> Dict[str, Any]:
        """
        Retrieves finished video URL.
        Returns dict with: {'video_url': str, 'duration': Optional[float]}
        """
        pass
