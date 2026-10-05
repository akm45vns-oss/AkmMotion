import sys
import io

# Force stdout & stderr to UTF-8 encoding on Windows to prevent UnicodeEncodeError on emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import time
import uuid
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

logger = logging.getLogger("akmmotion.access")

is_prod = settings.ENVIRONMENT.lower() in ["production", "prod"]
show_docs = not is_prod or settings.ENABLE_API_DOCS

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json" if show_docs else None,
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None
)

# Structured Request Logging & Request-ID Middleware
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    response.headers["X-Request-ID"] = request_id
    
    # Sanitize path to avoid leaking sensitive query params
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f'{{"request_id": "{request_id}", "method": "{request.method}", "path": "{request.url.path}", "status": {response.status_code}, "duration_ms": {duration_ms}, "ip": "{client_ip}"}}'
    )

    # Record Prometheus metrics
    try:
        from app.core.metrics import record_http_request
        record_http_request(request.method, request.url.path, response.status_code, duration_ms / 1000.0)
    except Exception:
        pass

    return response

# Global Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    is_https = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
        or is_prod
    )
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response

# Global Exception Sanitization Handler (blocks leaking DB / stack details in production)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    import logging
    logging.getLogger("uvicorn.error").error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    if is_prod:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please contact support."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Set up CORS
# Build origins list: always include localhost + any extra origins from env
_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://akm-motion.vercel.app",
]
# Append any additional origins from the ALLOWED_ORIGINS env variable
for _o in settings.cors_origins:
    if _o not in _cors_origins:
        _cors_origins.append(_o)

from app.core.profiler import PerformanceProfilingMiddleware

app.add_middleware(PerformanceProfilingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://akm-motion(-[a-z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    """Ensure all 28 database tables are created and guest user is seeded."""
    # Validate that required secrets are configured before touching the DB
    settings.validate_required_secrets

    try:
        import app.models.models
        import app.models.character
        from app.db.base import Base
        from app.db.session import engine, AsyncSessionLocal
        from sqlalchemy import text

        # 1. Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[Startup] All database tables verified / created successfully.")

        # 2. Seed the guest user so guest sessions can create projects (FK requirement)
        GUEST_USER_ID = "595744ab-c375-4bec-a3c0-429113163fe1"
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT id FROM users WHERE id = :uid LIMIT 1"),
                {"uid": GUEST_USER_ID}
            )
            if not result.fetchone():
                await session.execute(
                    text("""
                        INSERT INTO users (id, email, full_name, is_active, is_verified, auth_provider, created_at, updated_at)
                        VALUES (:uid, 'guest@akmmotion.ai', 'Guest Studio', true, true, 'email', NOW(), NOW())
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {"uid": GUEST_USER_ID}
                )
                await session.commit()
                print("[Startup] Guest user seeded successfully.")
            else:
                print("[Startup] Guest user already exists.")


    except Exception as e:
        print(f"[Startup] Notice during database init: {e}")


@app.get("/")
async def root():
    return {
        "message": "Welcome to AkmMotion AI Video SaaS API",
        "docs": "/docs",
        "health": "/health/live",
        "ready": "/health/ready",
        "metrics": "/metrics"
    }


@app.get("/metrics", tags=["Observability"])
async def prometheus_metrics():
    """Prometheus metrics endpoint for production monitoring and scraping."""
    from app.core.metrics import render_prometheus_metrics
    return Response(
        content=render_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Kubernetes / Render shallow liveness probe."""
    return {
        "status": "alive",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Readiness probe checking database, redis, and storage dependencies."""
    checks = {}
    is_ready = True

    # 1. Database check
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": "Database connection failed"}
        is_ready = False

    # 2. Redis check
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception:
        # Non-fatal because background task fallback is automatically active
        checks["redis"] = {"status": "degraded", "fallback": "background_tasks_active"}

    # 3. Storage check
    try:
        from app.services.storage_service import storage_service
        import os
        if settings.LOCAL_STORAGE:
            writable = os.access(storage_service.local_dir, os.W_OK)
            checks["storage"] = {"status": "healthy" if writable else "degraded", "type": "local"}
        else:
            checks["storage"] = {"status": "configured", "type": "cloud"}
    except Exception as e:
        checks["storage"] = {"status": "degraded", "error": str(e)}

    # 4. AI Provider health
    try:
        from app.services.ai.providers.provider_manager import provider_manager
        checks["ai_providers"] = provider_manager.get_health_summary()
    except Exception:
        checks["ai_providers"] = {"status": "unknown"}

    overall_status = "ready" if is_ready else "not_ready"
    status_code = 200 if is_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.get("/health/stats", tags=["Health"])
async def health_stats():
    """Observability stats: capacity, queue depth, providers, and storage usage."""
    from app.services.storage_service import storage_service
    from app.services.ai.providers.provider_manager import provider_manager
    from app.db.session import AsyncSessionLocal
    from app.repositories.render_repo import RenderRepository

    active_renders = 0
    try:
        async with AsyncSessionLocal() as db:
            repo = RenderRepository(db)
            active_renders = await repo.count_active_jobs_global()
    except Exception:
        pass

    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "active_global_renders": active_renders,
        "max_concurrent_renders": settings.MAX_CONCURRENT_RENDERS_GLOBAL,
        "storage": storage_service.calculate_storage_usage(),
        "providers": provider_manager.get_health_summary(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)