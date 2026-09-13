from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import RenderJob, Video, RenderStatus, Export, VideoQuality, ExportFormat


class RenderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: UUID) -> Optional[RenderJob]:
        query = select(RenderJob).where(RenderJob.id == job_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_job(self, project_id: UUID, user_id: UUID) -> Optional[RenderJob]:
        query = (
            select(RenderJob)
            .where(
                RenderJob.project_id == project_id,
                RenderJob.user_id == user_id,
                RenderJob.status.in_([RenderStatus.pending, RenderStatus.processing])
            )
            .order_by(RenderJob.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_video_by_job(self, job_id: UUID) -> Optional[Video]:
        query = select(Video).where(Video.render_job_id == job_id).order_by(Video.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_project(self, project_id: UUID, user_id: UUID) -> List[RenderJob]:
        query = (
            select(RenderJob)
            .where(RenderJob.project_id == project_id, RenderJob.user_id == user_id)
            .order_by(RenderJob.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_job(self, project_id: UUID, user_id: UUID, estimated_seconds: int = 15) -> RenderJob:
        job = RenderJob(
            project_id=project_id,
            user_id=user_id,
            status=RenderStatus.pending,
            progress=0,
            estimated_seconds=estimated_seconds,
            started_at=None
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update_progress(self, job_id: UUID, progress: int, status: Optional[RenderStatus] = None, error_message: Optional[str] = None) -> Optional[RenderJob]:
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.progress = progress
        if status:
            job.status = status
            if status == RenderStatus.processing and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            elif status in [RenderStatus.completed, RenderStatus.failed, RenderStatus.cancelled]:
                job.completed_at = datetime.now(timezone.utc)
        if error_message:
            job.error_message = error_message

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def create_video_and_export(
        self, project_id: UUID, user_id: UUID, job_id: UUID, video_url: str, duration: float, file_size: int = 10485760
    ) -> Video:
        video = Video(
            project_id=project_id,
            render_job_id=job_id,
            url=video_url,
            storage_path=f"videos/{project_id}.mp4",
            duration=duration,
            width=1080,
            height=1920,
            file_size=file_size,
            format="mp4"
        )
        self.db.add(video)
        await self.db.flush()

        # Create export record
        from datetime import timedelta
        export_item = Export(
            video_id=video.id,
            user_id=user_id,
            format=ExportFormat.mp4,
            quality=VideoQuality.res_1080p,
            url=video_url,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        self.db.add(export_item)

        await self.db.commit()
        await self.db.refresh(video)
        return video
