from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.render_repo import RenderRepository
from app.schemas.render import RenderJobResponse, VideoResponse
from app.services.render_engine import RenderEngineService
from app.models.models import RenderStatus, ProjectStatus
from app.repositories.project_repo import ProjectRepository


class RenderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RenderRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.engine = RenderEngineService()

    async def start_render_job(self, project_id: UUID, user_id_str: str) -> RenderJobResponse:
        user_id = UUID(user_id_str)
        from app.core.dependencies import ensure_user_in_db
        await ensure_user_in_db(self.db, user_id)

        project = await self.proj_repo.get_by_id(project_id, user_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Create Render Job in DB
        job = await self.repo.create_job(project_id=project_id, user_id=user_id, estimated_seconds=15)
        
        # Mark job as processing & execute render async
        await self.execute_render(job.id, project_id, user_id)
        
        updated_job = await self.repo.get_by_id(job.id)
        return RenderJobResponse.model_validate(updated_job)

    async def execute_render(self, job_id: UUID, project_id: UUID, user_id: UUID):
        await self.repo.update_progress(job_id, progress=10, status=RenderStatus.processing)

        async def on_progress(percentage: int, message: str):
            await self.repo.update_progress(job_id, progress=percentage)

        # Run render engine compilation
        final_url = await self.engine.compile_video(
            scenes_data=[],
            output_path="",
            progress_callback=on_progress
        )

        # Create Video record
        video = await self.repo.create_video_and_export(
            project_id=project_id,
            user_id=user_id,
            job_id=job_id,
            video_url=final_url,
            duration=15.0
        )

        # Update job to completed
        await self.repo.update_progress(job_id, progress=100, status=RenderStatus.completed)

    async def get_job_status(self, job_id: UUID, user_id_str: Optional[str] = None) -> RenderJobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")
        if user_id_str is not None:
            user_uuid = UUID(str(user_id_str))
            if job.user_id != user_uuid:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")
        return RenderJobResponse.model_validate(job)
