import logging
from typing import Dict, Any, Optional

from app.services.ai.providers.base import VideoGenerationProvider, ProviderState
from app.services.ai.providers.fal_provider import FalProvider
from app.services.ai.providers.fallback_provider import FallbackProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Central manager for AI video generation and scene animation providers.
    Directs generation requests to the best healthy provider with seamless failover.
    """

    def __init__(self):
        self.fal = FalProvider()
        self.fallback = FallbackProvider()
        self.providers = {
            self.fal.name: self.fal,
            self.fallback.name: self.fallback
        }

    def get_provider(self, name: Optional[str] = None) -> VideoGenerationProvider:
        if name and name in self.providers:
            return self.providers[name]

        # Automatic provider selection based on health
        if self.fal.state == ProviderState.HEALTHY:
            return self.fal
        elif self.fal.state == ProviderState.DEGRADED:
            logger.warning("[ProviderManager] fal.ai is DEGRADED. Routing to fallback Ken Burns provider.")
            return self.fallback
        else:
            return self.fallback

    def get_health_summary(self) -> Dict[str, str]:
        return {p_name: p.state.value for p_name, p in self.providers.items()}


provider_manager = ProviderManager()
