import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AkmMotion API"
    VERSION: str = "1.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ENABLE_API_DOCS: bool = False

    # App URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
    TRUSTED_PROXIES: str = "127.0.0.1,::1,localhost,testclient"
    INTERNAL_GATEWAY_KEY: str = ""

    @property
    def trusted_proxy_list(self) -> List[str]:
        return [p.strip() for p in self.TRUSTED_PROXIES.split(",") if p.strip()]

    # Neon PostgreSQL Database
    # REQUIRED: Set in .env — never hardcode credentials here.
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 300
    PERFORMANCE_PROFILING_ENABLED: bool = False

    # Cloudflare R2 / S3 Storage Credentials
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "akmmotion-storage"

    # JWT Authentication
    # REQUIRED: Must be a cryptographically random string of at least 32 characters.
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # Backward-compatible default
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    INACTIVITY_TIMEOUT_SECONDS: int = 180  # 3 minutes

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_WORKER_CONCURRENCY: int = 2
    # Render Execution Mode: 'background' (dev) or 'celery' (prod mandatory)
    RENDER_EXECUTION_MODE: str = "background"

    # Capacity Controls & Concurrency Limits
    MAX_CONCURRENT_RENDERS_GLOBAL: int = 5
    MAX_CONCURRENT_RENDERS_PER_USER: int = 1
    MAX_QUEUED_JOBS_PER_USER: int = 3
    MAX_SCENES_PER_RENDER: int = 50
    MAX_RENDER_DURATION_SECONDS: int = 600
    MAX_SIMULTANEOUS_AI_GENERATIONS: int = 3
    RENDER_TIMEOUT_SECONDS: int = 600

    # Subtitle Timing Mode: 'heuristic' (default) or 'acoustic'
    TIMING_MODE: str = "heuristic"

    # Storage Settings
    LOCAL_STORAGE: bool = True
    STORAGE_BASE_URL: str = ""
    SIGNED_URL_EXPIRATION_SECONDS: int = 3600

    # Cost Controls & Quota Limits
    MAX_PROJECTS_PER_USER: int = 25
    MAX_SCENES_PER_PROJECT: int = 50
    MAX_SCRIPT_LENGTH: int = 5000
    MAX_DAILY_AI_REQUESTS: int = 50
    MAX_DAILY_VIDEO_GENERATIONS: int = 10
    MAX_STORAGE_BYTES_PER_USER: int = 1073741824  # 1 GB

    # External AI APIs
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
    # fal.ai Text-to-Video
    FAL_KEY: str = ""
    FAL_VIDEO_MODEL: str = "fal-ai/kling-video/v1/standard/text-to-video"
    FAL_VIDEO_ENABLED: bool = True
    # Groq API keys — all 5 used for round-robin rotation & rate-limit failover
    GROQ_API_KEY:   str = ""  # Primary
    GROQ_API_KEY_2: str = ""
    GROQ_API_KEY_3: str = ""
    GROQ_API_KEY_4: str = ""
    GROQ_API_KEY_5: str = ""

    @property
    def groq_keys(self) -> list[str]:
        """Returns all configured Groq API keys (non-empty only)."""
        return [
            k for k in [
                self.GROQ_API_KEY, self.GROQ_API_KEY_2, self.GROQ_API_KEY_3,
                self.GROQ_API_KEY_4, self.GROQ_API_KEY_5
            ] if k and k.startswith("gsk_")
        ]

    # Rendering Executables
    FFMPEG_PATH: str = "ffmpeg"
    REMOTION_PATH: str = "npx remotion"
    STORAGE_DIR: str = ""

    @property
    def video_storage_dir(self) -> str:
        if self.STORAGE_DIR:
            path = os.path.join(self.STORAGE_DIR, "videos")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(base_dir, "storage", "videos")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def validate_required_secrets(self) -> None:
        """
        Call at application startup to enforce that critical secrets are set.
        Raises RuntimeError immediately if any required secret is missing or insecure.
        """
        errors = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is not set. Set it in .env or environment variables.")
        if not self.JWT_SECRET:
            errors.append("JWT_SECRET is not set. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
        elif len(self.JWT_SECRET) < 32:
            errors.append(f"JWT_SECRET is too short ({len(self.JWT_SECRET)} chars). Minimum 32 characters required.")
        if self.ENVIRONMENT.lower() == "production":
            if self.RENDER_EXECUTION_MODE.lower() != "celery":
                errors.append(
                    f"RENDER_EXECUTION_MODE must be set to 'celery' in production (got '{self.RENDER_EXECUTION_MODE}'). "
                    "BackgroundTasks in-process execution is strictly forbidden in production."
                )
            if not self.CELERY_BROKER_URL or "CHANGE_ME" in self.CELERY_BROKER_URL:
                errors.append("CELERY_BROKER_URL must be configured with a valid broker URL in production.")
            if self.CELERY_TASK_ALWAYS_EAGER:
                errors.append("CELERY_TASK_ALWAYS_EAGER cannot be enabled in production.")

        if errors:
            raise RuntimeError(
                "[AkmMotion] FATAL: Required secrets or production settings are missing or insecure.\n" +
                "\n".join(f"  [!] {e}" for e in errors)
            )

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()