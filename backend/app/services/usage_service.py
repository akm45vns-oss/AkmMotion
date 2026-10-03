import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.models import UserUsage, Project, Scene

logger = logging.getLogger(__name__)


class UsageService:
    """
    Cost control and abuse protection service.
    Tracks resource utilization per tenant/user and enforces configurable capacity quotas.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_usage(self, user_id: UUID) -> UserUsage:
        query = select(UserUsage).where(UserUsage.user_id == user_id)
        result = await self.db.execute(query)
        usage = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not usage:
            usage = UserUsage(
                user_id=user_id,
                ai_requests_today=0,
                video_generations_today=0,
                render_jobs_today=0,
                rendered_seconds_total=0.0,
                storage_bytes_total=0,
                estimated_cost_cents=0,
                last_reset_date=now
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
            return usage

        # Check if daily reset is needed
        last_reset = usage.last_reset_date
        if last_reset.tzinfo is None:
            last_reset = last_reset.replace(tzinfo=timezone.utc)

        if last_reset.date() < now.date():
            usage.ai_requests_today = 0
            usage.video_generations_today = 0
            usage.render_jobs_today = 0
            usage.last_reset_date = now
            await self.db.commit()
            await self.db.refresh(usage)

        return usage

    async def reserve_quota(
        self,
        user_id: UUID,
        field_name: str,
        max_limit: int,
        estimated_cost_cents: int = 0
    ) -> UserUsage:
        """
        Atomically checks and reserves a quota credit within a database transaction
        using PostgreSQL row-level locking (SELECT ... FOR UPDATE).
        Eliminates race conditions and double-spending across concurrent workers and processes.
        """
        # Ensure row exists first
        await self.get_or_create_usage(user_id)

        # Acquire exclusive row lock
        query = select(UserUsage).where(UserUsage.user_id == user_id).with_for_update()
        result = await self.db.execute(query)
        usage = result.scalar_one()

        now = datetime.now(timezone.utc)
        last_reset = usage.last_reset_date
        if last_reset.tzinfo is None:
            last_reset = last_reset.replace(tzinfo=timezone.utc)

        # Handle midnight UTC rollover under lock
        if last_reset.date() < now.date():
            usage.ai_requests_today = 0
            usage.video_generations_today = 0
            usage.render_jobs_today = 0
            usage.last_reset_date = now

        current_val = getattr(usage, field_name, 0)
        if current_val >= max_limit:
            readable_name = field_name.replace("_", " ").replace("today", "").strip().title()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily {readable_name} limit reached ({current_val}/{max_limit}). Quota resets at midnight UTC."
            )

        # Atomically increment
        setattr(usage, field_name, current_val + 1)
        if estimated_cost_cents > 0:
            usage.estimated_cost_cents += estimated_cost_cents

        await self.db.commit()
        await self.db.refresh(usage)
        return usage

    async def release_quota(
        self,
        user_id: UUID,
        field_name: str,
        estimated_cost_cents: int = 0
    ) -> None:
        """
        Atomically releases a previously reserved quota credit if the downstream
        operation fails before consuming external provider units.
        """
        query = select(UserUsage).where(UserUsage.user_id == user_id).with_for_update()
        result = await self.db.execute(query)
        usage = result.scalar_one_or_none()
        if not usage:
            return

        current_val = getattr(usage, field_name, 0)
        setattr(usage, field_name, max(0, current_val - 1))
        if estimated_cost_cents > 0:
            usage.estimated_cost_cents = max(0, usage.estimated_cost_cents - estimated_cost_cents)

        await self.db.commit()

    async def reserve_video_generation(self, user_id: UUID, estimated_cost_cents: int = 10) -> UserUsage:
        return await self.reserve_quota(
            user_id, "video_generations_today", settings.MAX_DAILY_VIDEO_GENERATIONS, estimated_cost_cents
        )

    async def release_video_generation(self, user_id: UUID, estimated_cost_cents: int = 10) -> None:
        await self.release_quota(user_id, "video_generations_today", estimated_cost_cents)

    async def reserve_ai_request(self, user_id: UUID, estimated_cost_cents: int = 1) -> UserUsage:
        return await self.reserve_quota(
            user_id, "ai_requests_today", settings.MAX_DAILY_AI_REQUESTS, estimated_cost_cents
        )

    async def release_ai_request(self, user_id: UUID, estimated_cost_cents: int = 1) -> None:
        await self.release_quota(user_id, "ai_requests_today", estimated_cost_cents)

    async def check_ai_request_limit(self, user_id: UUID):
        usage = await self.get_or_create_usage(user_id)
        if usage.ai_requests_today >= settings.MAX_DAILY_AI_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily AI generation limit reached ({usage.ai_requests_today}/{settings.MAX_DAILY_AI_REQUESTS}). Quota resets at midnight UTC."
            )

    async def check_video_generation_limit(self, user_id: UUID):
        usage = await self.get_or_create_usage(user_id)
        if usage.video_generations_today >= settings.MAX_DAILY_VIDEO_GENERATIONS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily video generation limit reached ({usage.video_generations_today}/{settings.MAX_DAILY_VIDEO_GENERATIONS}). Please upgrade your plan or wait until tomorrow."
            )

    async def check_project_limit(self, user_id: UUID):
        from sqlalchemy import func
        count_query = select(func.count(Project.id)).where(Project.user_id == user_id)
        res = await self.db.execute(count_query)
        project_count = res.scalar() or 0
        if project_count >= settings.MAX_PROJECTS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project quota exceeded ({project_count}/{settings.MAX_PROJECTS_PER_USER}). Please delete old projects to create new ones."
            )

    async def record_ai_request(self, user_id: UUID, estimated_cost_cents: int = 1):
        usage = await self.get_or_create_usage(user_id)
        usage.ai_requests_today += 1
        usage.estimated_cost_cents += estimated_cost_cents
        await self.db.commit()

    async def record_video_generation(self, user_id: UUID, estimated_cost_cents: int = 10):
        usage = await self.get_or_create_usage(user_id)
        usage.video_generations_today += 1
        usage.estimated_cost_cents += estimated_cost_cents
        await self.db.commit()

    async def record_render_completion(self, user_id: UUID, duration_seconds: float, file_size_bytes: int):
        usage = await self.get_or_create_usage(user_id)
        usage.render_jobs_today += 1
        usage.rendered_seconds_total += duration_seconds
        usage.storage_bytes_total += file_size_bytes
        # 1 cent per 10 seconds of rendering
        usage.estimated_cost_cents += int(duration_seconds / 10)
        await self.db.commit()
