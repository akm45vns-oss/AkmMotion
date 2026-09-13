from typing import Dict, Callable
from fastapi import HTTPException, status, Request
from collections import defaultdict
import time
from datetime import timedelta

# Simple in-memory rate limiter for production-safe protection
# For distributed deployments, this should be replaced with Redis-based rate limiting
class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) >= max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

    def reset(self) -> None:
        """Resets all request history (useful for test isolation)."""
        self.requests.clear()

# Global rate limiter instance
_rate_limiter = RateLimiter()

def extract_rate_limit_key(request: Request) -> str:
    """
    Extracts an isolated rate limiting key based on user ID, auth token,
    guest session cookie/header, or client IP.
    """
    # 1. Explicit user header (internal/gateway)
    user_header = request.headers.get("X-User-ID")
    if user_header:
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

    # 4. Fallback to client host (support reverse proxies / CDN headers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Real-IP")
            or (request.client.host if request.client else "unknown")
        )
    return f"ip:{client_ip}"

def check_rate_limit(request: Request, max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limiting dependency for FastAPI endpoints.
    Limits requests per user/session within a time window.
    """
    rate_key = extract_rate_limit_key(request)
    
    if not _rate_limiter.is_allowed(rate_key, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds"
        )
    
    return True

# Rate limiter class for dependency injection
class RateLimitDependency:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def __call__(self, request: Request) -> bool:
        return check_rate_limit(request, self.max_requests, self.window_seconds)

# Pre-configured rate limit dependencies
rate_limit_script_ai = RateLimitDependency(20, 60)
rate_limit_tts = RateLimitDependency(30, 60)
rate_limit_image_gen = RateLimitDependency(15, 60)
rate_limit_pipeline = RateLimitDependency(5, 60)

