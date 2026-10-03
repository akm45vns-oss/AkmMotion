import time
from typing import Optional
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

# 1. HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "akmmotion_http_requests_total",
    "Total HTTP requests received",
    ["method", "path", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "akmmotion_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

ACTIVE_REQUESTS = Gauge(
    "akmmotion_active_requests",
    "Number of currently active in-flight HTTP requests"
)

# 2. Render Pipeline Metrics
RENDER_JOBS_TOTAL = Counter(
    "akmmotion_render_jobs_total",
    "Total render jobs submitted, categorized by status",
    ["status"]  # submitted, completed, failed, cancelled
)

RENDER_DURATION_SECONDS = Histogram(
    "akmmotion_render_duration_seconds",
    "FFmpeg render job duration in seconds",
    buckets=(1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0, 120.0, 180.0, 300.0)
)

ACTIVE_RENDER_JOBS = Gauge(
    "akmmotion_active_render_jobs",
    "Number of currently active rendering jobs"
)

# 3. AI Provider Metrics
AI_PROVIDER_REQUESTS_TOTAL = Counter(
    "akmmotion_ai_provider_requests_total",
    "Total outbound AI provider requests",
    ["provider", "service_type", "status"]  # provider: openai, groq, fal, edgetts, gtts
)

AI_PROVIDER_DURATION_SECONDS = Histogram(
    "akmmotion_ai_provider_duration_seconds",
    "Outbound AI provider latency in seconds",
    ["provider", "service_type"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
)

# 4. Quota & Financial Guardrail Metrics
QUOTA_OPERATIONS_TOTAL = Counter(
    "akmmotion_quota_operations_total",
    "Quota reservation and release operations",
    ["operation", "status"]  # operation: reserve, release; status: success, exhausted
)

# 5. Storage Gauge
STORAGE_USAGE_BYTES = Gauge(
    "akmmotion_storage_usage_bytes",
    "Total persistent storage bytes consumed",
    ["storage_type"]  # local, cloud
)


def sanitize_metrics_path(path: str) -> str:
    """
    Collapses dynamic UUIDs and path parameters to prevent high-cardinality metric explosion.
    Example: /api/v1/projects/595744ab-c375-4bec-a3c0-429113163fe1 -> /api/v1/projects/{id}
    """
    parts = path.strip("/").split("/")
    sanitized = []
    for part in parts:
        # Check if part is UUID or hex
        if len(part) in (32, 36) and ("-" in part or all(c in "0123456789abcdefABCDEF" for c in part)):
            sanitized.append("{id}")
        else:
            sanitized.append(part)
    return "/" + "/".join(sanitized) if sanitized else "/"


def record_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Records an incoming HTTP request in Prometheus counters and histograms."""
    clean_path = sanitize_metrics_path(path)
    HTTP_REQUESTS_TOTAL.labels(
        method=method.upper(),
        path=clean_path,
        status_code=str(status_code)
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method.upper(),
        path=clean_path
    ).observe(duration_seconds)


def render_prometheus_metrics() -> bytes:
    """Renders latest Prometheus metrics payload in standard UTF-8 text format."""
    return generate_latest(REGISTRY)
