"""
Request-Level Performance Profiler & Telemetry Tracer
Controlled via `settings.PERFORMANCE_PROFILING_ENABLED`.
When False: completely zero-overhead pass-through.
When True: instruments request phase timings (middleware, auth, db, service, serialization)
and injects Server-Timing headers for fine-grained bottleneck diagnosis.
"""

import time
import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.config import settings

logger = logging.getLogger("app.profiler")

# Context-local storage for correlated span timings
_current_trace: ContextVar[Optional[Dict[str, Any]]] = ContextVar("_current_trace", default=None)


class RequestProfiler:
    """Helper context manager to measure named execution blocks within a request."""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.t0: float = 0.0

    def __enter__(self):
        if not settings.PERFORMANCE_PROFILING_ENABLED:
            return self
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not settings.PERFORMANCE_PROFILING_ENABLED:
            return
        dur_ms = (time.perf_counter() - self.t0) * 1000.0
        trace = _current_trace.get()
        if trace is not None:
            trace["spans"][self.stage_name] = round(dur_ms, 2)


def profile_span(stage_name: str):
    """Convenience factory for timing spans."""
    return RequestProfiler(stage_name)


class PerformanceProfilingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that measures end-to-end request phases when enabled."""

    async def dispatch(self, request: Request, call_next):
        if not settings.PERFORMANCE_PROFILING_ENABLED:
            return await call_next(request)

        req_id = request.headers.get("X-Request-ID", "unknown")
        user_id = request.headers.get("X-User-ID", "anonymous")
        trace_data: Dict[str, Any] = {
            "request_id": req_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "spans": {}
        }
        token = _current_trace.set(trace_data)

        t_start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            total_dur_ms = (time.perf_counter() - t_start) * 1000.0
            trace_data["total_ms"] = round(total_dur_ms, 2)

            # Build Server-Timing header for browser & test client introspection
            server_timing_parts = [f"total;dur={round(total_dur_ms, 2)}"]
            for span_name, span_dur in trace_data["spans"].items():
                server_timing_parts.append(f"{span_name};dur={span_dur}")
            
            response.headers["Server-Timing"] = ", ".join(server_timing_parts)
            response.headers["X-Trace-Total-Ms"] = str(round(total_dur_ms, 2))

            if total_dur_ms > 1000.0:
                logger.warning(f"[SlowRequest] {request.method} {request.url.path} took {total_dur_ms:.1f}ms: {trace_data['spans']}")

            return response
        finally:
            _current_trace.reset(token)
