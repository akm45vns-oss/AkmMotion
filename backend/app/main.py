import sys
import io

# Force stdout & stderr to UTF-8 encoding on Windows to prevent UnicodeEncodeError on emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    """Ensure all 28 database tables and schema are automatically created on startup."""
    try:
        import app.models.models
        import app.models.character
        from app.db.base import Base
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[Startup] All database tables verified / created successfully.")
    except Exception as e:
        print(f"[Startup] Notice during database auto-init: {e}")


@app.get("/")
async def root():
    return {
        "message": "Welcome to AkmMotion AI Video SaaS API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)