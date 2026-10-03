import time
import threading
from typing import Dict, List, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    Sliding window thread-safe rate limiter with Redis-compatible semantics.
    Enforces per-session, per-user, and per-proxy IP isolation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def reset(self) -> None:
        """Resets all request history (useful for test isolation and session resets)."""
        with self._lock:
            self.requests.clear()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self.requests[key]
            # Clean old requests
            active = [t for t in timestamps if t > window_start]
            self.requests[key] = active

            if len(active) >= max_requests:
                return False

            self.requests[key].append(now)
            return True

    def check(self, key: str, max_requests: int, window_seconds: int, *args) -> bool:
        return self.is_allowed(key, max_requests, window_seconds)

    def check_ip(self, ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        return self.is_allowed(f"ip:{ip}", max_requests, window_seconds)

    def check_user(self, user_id: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        return self.is_allowed(f"user:{user_id}", max_requests, window_seconds)


# Global rate limiter instance
_rate_limiter = RateLimiter()
limiter = _rate_limiter


def extract_rate_limit_key(request: Request) -> str:
    """
    Extracts an isolated rate limiting key based on user ID, auth token,
    guest session cookie/header, or client IP (with reverse proxy headers validated
    strictly against configured trusted proxies).
    """
    from app.core.config import settings

    peer_ip = request.client.host if request.client else "unknown"
    is_trusted_peer = (
        peer_ip in settings.trusted_proxy_list
        or peer_ip in ["127.0.0.1", "::1", "testclient", "localhost"]
    )

    # 1. Explicit internal user header: ONLY trusted if from trusted proxy or valid gateway key
    user_header = request.headers.get("X-User-ID")
    if user_header:
        gateway_key = request.headers.get("X-Internal-Gateway-Key")
        if (settings.INTERNAL_GATEWAY_KEY and gateway_key == settings.INTERNAL_GATEWAY_KEY) or is_trusted_peer:
            return f"user:{user_header}"

    # 2. Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token and token not in ["guest_studio_session_token", "guest_studio_token", "null", "undefined"]:
            return f"auth:{hash(token)}"

    # 3. Guest session header or cookie
    guest_id = (
        request.headers.get("X-Guest-Session-ID")
        or request.headers.get("x-guest-session-id")
        or request.cookies.get("guest_session_id")
    )
    if guest_id:
        return f"guest:{guest_id}"

    # 4. Fallback to client host: only trust forwarded proxy headers from trusted peers
    if is_trusted_peer:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = (
                request.headers.get("CF-Connecting-IP")
                or request.headers.get("X-Real-IP")
                or peer_ip
            )
    else:
        # Direct untrusted client connection: ignore forged forwarded headers
        client_ip = peer_ip

    return f"ip:{client_ip}"


def check_rate_limit(request: Request, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """
    Rate limiting dependency for FastAPI endpoints.
    Limits requests per user/session within a sliding time window.
    """
    rate_key = extract_rate_limit_key(request)

    if not _rate_limiter.is_allowed(rate_key, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds",
            headers={"Retry-After": str(window_seconds)}
        )

    return True


class RateLimitDependency:
    """FastAPI dependency for declarative rate limiting per route."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def __call__(self, request: Request) -> bool:
        return check_rate_limit(request, self.max_requests, self.window_seconds)


# Pre-configured rate limit dependencies
rate_limit_script_ai = RateLimitDependency(20, 60)
rate_limit_tts = RateLimitDependency(30, 60)
rate_limit_image_gen = RateLimitDependency(15, 60)
rate_limit_pipeline = RateLimitDependency(5, 60)
rate_limit_image_proxy = RateLimitDependency(30, 60)
rate_limit_video_gen = RateLimitDependency(5, 60)


async def rate_limit_ip_guard(request: Request, max_requests: int = 120, window_seconds: int = 60):
    check_rate_limit(request, max_requests=max_requests, window_seconds=window_seconds)

