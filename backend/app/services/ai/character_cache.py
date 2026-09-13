import time
from typing import Dict, Any, Optional


class CharacterCache:
    """
    High-performance in-memory cache for Character DNA objects.
    Guarantees character lookup and prompt injection latency < 100ms.
    """
    _cache: Dict[str, Dict[str, Any]] = {}
    _timestamps: Dict[str, float] = {}
    TTL_SECONDS: float = 3600.0  # 1 hour cache TTL

    @classmethod
    def set(cls, character_id: str, dna_dict: Dict[str, Any]) -> None:
        cls._cache[character_id] = dna_dict
        cls._timestamps[character_id] = time.time()

    @classmethod
    def get(cls, character_id: str) -> Optional[Dict[str, Any]]:
        if character_id in cls._cache:
            created_time = cls._timestamps.get(character_id, 0)
            if time.time() - created_time < cls.TTL_SECONDS:
                return cls._cache[character_id]
            else:
                # Expired
                cls.invalidate(character_id)
        return None

    @classmethod
    def invalidate(cls, character_id: str) -> None:
        cls._cache.pop(character_id, None)
        cls._timestamps.pop(character_id, None)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
        cls._timestamps.clear()