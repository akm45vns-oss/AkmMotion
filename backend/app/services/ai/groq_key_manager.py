"""
GroqKeyManager — Round-robin API key rotation with automatic rate-limit failover.

Strategy for 5 Groq keys:
- Each key gets its own Groq async client (pre-instantiated for speed)
- Round-robin selection: key index increments on every successful call
- On 429 (rate limit) or any quota error → immediately try next key
- Exhausted keys are put on a 60s cooldown and retried afterward
- Parallel calls across different scenes will naturally spread across keys
- Best model: llama-3.3-70b-versatile (128k ctx, best quality on Groq free tier)
"""

import time
import asyncio
import threading
from typing import List, Optional, Dict
from app.core.config import settings


class _KeyState:
    __slots__ = ("key", "client", "fail_count", "cooldown_until")

    def __init__(self, key: str):
        self.key = key
        self.client = None          # lazy-init AsyncGroq
        self.fail_count: int = 0
        self.cooldown_until: float = 0.0

    def is_available(self) -> bool:
        return time.monotonic() >= self.cooldown_until

    def mark_failed(self):
        self.fail_count += 1
        # Exponential back-off: 60s, 120s, 240s … max 10 min
        cooldown = min(60 * (2 ** (self.fail_count - 1)), 600)
        self.cooldown_until = time.monotonic() + cooldown

    def mark_success(self):
        self.fail_count = 0
        self.cooldown_until = 0.0

    def get_client(self):
        if self.client is None:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=self.key)
        return self.client


class GroqKeyManager:
    """
    Thread-safe round-robin Groq key manager with failover.
    Usage:
        manager = GroqKeyManager.get_instance()
        result  = await manager.chat(messages=[...], model="llama-3.3-70b-versatile")
    """

    # Singleton
    _instance: Optional["GroqKeyManager"] = None
    _lock = threading.Lock()

    # Best available Groq models (ordered by quality)
    BEST_MODEL   = "openai/gpt-oss-120b"        # 120B parameter state-of-the-art model
    FAST_MODEL   = "qwen/qwen3.8-27b"           # Top quality multilingual & storytelling
    BACKUP_MODEL = "openai/gpt-oss-20b"          # Fast fallback model
    VISION_MODEL = "meta-llama/llama-prompt-guard-2-86m"

    @classmethod
    def get_instance(cls) -> "GroqKeyManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        keys = settings.groq_keys
        if not keys:
            raise RuntimeError(
                "No Groq API keys configured. Add GROQ_API_KEY ... GROQ_API_KEY_5 to .env"
            )
        self._states: List[_KeyState] = [_KeyState(k) for k in keys]
        self._index: int = 0
        self._mutex = asyncio.Lock()
        print(f"[GroqKeyManager] Initialized with {len(self._states)} key(s). "
              f"Best model: {self.BEST_MODEL}")

    def _pick_key(self) -> Optional[_KeyState]:
        """Select the next available key using round-robin."""
        n = len(self._states)
        for _ in range(n):
            state = self._states[self._index % n]
            self._index = (self._index + 1) % n
            if state.is_available():
                return state
        return None  # All keys on cooldown

    async def chat(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.75,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        max_retries: int = 5,
    ) -> str:
        """
        Sends a chat completion request, rotating keys on failure.
        Returns the raw content string from the first successful response.
        Raises RuntimeError if all keys fail.
        """
        model = model or self.BEST_MODEL
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            state = self._pick_key()
            if state is None:
                # All keys cooling down — wait 5s and retry
                await asyncio.sleep(5)
                state = self._pick_key()
                if state is None:
                    raise RuntimeError("[GroqKeyManager] All Groq keys are on cooldown.")

            try:
                client = state.get_client()
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = await client.chat.completions.create(**kwargs)
                state.mark_success()
                return response.choices[0].message.content

            except Exception as e:
                err_str = str(e).lower()
                last_error = e

                # Rate limit / quota → cool this key down
                if any(kw in err_str for kw in ["rate_limit", "429", "quota", "too many"]):
                    print(f"[GroqKeyManager] Key ...{state.key[-6:]} rate-limited. "
                          f"Rotating to next key. (attempt {attempt + 1}/{max_retries})")
                    state.mark_failed()
                    continue

                # Auth error → permanently disable this key for the session
                if any(kw in err_str for kw in ["401", "invalid_api_key", "authentication"]):
                    print(f"[GroqKeyManager] Key ...{state.key[-6:]} invalid. Disabling.")
                    state.cooldown_until = float("inf")
                    continue

                # Model not found -> switch to fallback model
                if any(kw in err_str for kw in ["model_not_found", "does not exist"]):
                    print(f"[GroqKeyManager] Model {model} not found, falling back to {self.FAST_MODEL}")
                    model = self.FAST_MODEL if model != self.FAST_MODEL else self.BACKUP_MODEL
                    continue

                # Other error → brief cooldown + retry
                print(f"[GroqKeyManager] Key ...{state.key[-6:]} error: {e}. "
                      f"Retrying (attempt {attempt + 1}/{max_retries})")
                state.mark_failed()
                await asyncio.sleep(1)

        raise RuntimeError(
            f"[GroqKeyManager] All {max_retries} attempts failed. Last error: {last_error}"
        )

    async def chat_with_json(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.75,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience wrapper that enforces JSON output mode."""
        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

    def status(self) -> List[Dict]:
        """Returns current status of all keys (for debugging)."""
        now = time.monotonic()
        return [
            {
                "key_suffix": f"...{s.key[-6:]}",
                "available":  s.is_available(),
                "fail_count": s.fail_count,
                "cooldown_remaining": max(0, round(s.cooldown_until - now, 1))
            }
            for s in self._states
        ]
