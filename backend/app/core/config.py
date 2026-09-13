import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AkmMotion API"
    VERSION: str = "1.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # App URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"

    # Neon PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_pYKgFxNOA25E@ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"
    SYNC_DATABASE_URL: str = "postgresql://neondb_owner:npg_pYKgFxNOA25E@ep-wispy-waterfall-ay9ni5ea-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

    # Cloudflare R2 / S3 Storage Credentials
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "akmmotion-storage"

    # JWT Authentication
    JWT_SECRET: str = "super-secret-jwt-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # External AI APIs
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()