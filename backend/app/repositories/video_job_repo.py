from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import VideoGenerationJob, VideoGenerationStatus


class VideoJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: UUID) -> Optional[VideoGenerationJob]:
        query = select(VideoGenerationJob).where(VideoGenerationJob.id == job_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_job_for_scene(
        self, scene_id: UUID, stale_timeout_seconds: int = 600
    ) -> Optional[VideoGenerationJob]:
        """
        Returns an active (pending/in_queue/in_progress) job for a given scene.
        Includes stale auto-recovery if the job has been abandoned.
        """
        query = (
            select(VideoGenerationJob)
            .where(
                VideoGenerationJob.scene_id == scene_id,
                VideoGenerationJob.status.in_([
                    VideoGenerationStatus.pending.value,
                    VideoGenerationStatus.in_queue.value,
                    VideoGenerationStatus.in_progress.value
                ])
            )
            .order_by(VideoGenerationJob.created_at.desc())
        )
        result = await self.db.execute(query)
        job = result.scalars().first()
        if not job:
            return None

        # Stale recovery
        check_time = job.updated_at or job.created_at
        if check_time:
            if check_time.tzinfo is None:
                check_time = check_time.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - check_time).total_seconds()
            if age > stale_timeout_seconds:
                job.status = VideoGenerationStatus.failed.value
                job.error_message = "Generation timed out or connection was lost. Please try again."
                await self.db.commit()
                await self.db.refresh(job)
                return None

        return job

    async def create_job(
        self,
        scene_id: UUID,
        project_id: UUID,
        user_id: UUID,
        prompt: str,
        provider: str = "fal.ai",
        provider_request_id: Optional[str] = None,
        status_url: Optional[str] = None,
        response_url: Optional[str] = None,
        status: str = VideoGenerationStatus.pending.value
    ) -> VideoGenerationJob:
        job = VideoGenerationJob(
            scene_id=scene_id,
            project_id=project_id,
            user_id=user_id,
            provider=provider,
            provider_request_id=provider_request_id,
            status_url=status_url,
            response_url=response_url,
            status=status,
            prompt=prompt
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update_status(
        self,
        job: VideoGenerationJob,
        status: str,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> VideoGenerationJob:
        job.status = status
        if video_url is not None:
            job.video_url = video_url
        if error_message is not None:
            job.error_message = error_message
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_scene(self, scene_id: UUID) -> List[VideoGenerationJob]:
        query = (
            select(VideoGenerationJob)
            .where(VideoGenerationJob.scene_id == scene_id)
            .order_by(VideoGenerationJob.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
