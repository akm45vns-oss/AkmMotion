import os
import asyncio
import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, BackgroundTasks

from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.repositories.render_repo import RenderRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.render import RenderJobResponse
from app.services.render_engine import RenderEngineService
from app.models.models import RenderJob, RenderStatus, Project, Scene, SceneAsset, AssetType, Video

logger = logging.getLogger(__name__)


class RenderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RenderRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.engine = RenderEngineService()

    async def start_render_job(
        self,
        project_id: UUID,
        user_id_str: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> RenderJobResponse:
        user_id = UUID(user_id_str)
        from app.core.dependencies import ensure_user_in_db
        await ensure_user_in_db(self.db, user_id)

        project = await self.proj_repo.get_by_id(project_id, user_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Concurrency protection: return existing active job if already queued or processing
        active_job = await self.repo.get_active_job(project_id, user_id)
        if active_job:
            resp = RenderJobResponse.model_validate(active_job)
            video = await self.repo.get_video_by_job(active_job.id)
            if video:
                resp.video_url = video.url
            return resp

        # Create new Render Job in DB
        job = await self.repo.create_job(project_id=project_id, user_id=user_id, estimated_seconds=15)

        # Dispatch background render execution
        if background_tasks is not None:
            background_tasks.add_task(self.execute_render_background, job.id, project_id, user_id)
        else:
            asyncio.create_task(self.execute_render_background(job.id, project_id, user_id))

        updated_job = await self.repo.get_by_id(job.id)
        return RenderJobResponse.model_validate(updated_job or job)

    async def execute_render(self, job_id: UUID, project_id: UUID, user_id: UUID):
        """Direct execution wrapper for backward-compatibility."""
        await self.execute_render_background(job_id, project_id, user_id)

    @classmethod
    async def execute_render_background(cls, job_id: UUID, project_id: UUID, user_id: UUID):
        """
        Executes real video rendering in the background using an isolated database session.
        Loads project scenes, prepares assets, encodes 9:16 vertical MP4 via FFmpeg,
        and saves Video record with persistent output storage.
        """
        async with AsyncSessionLocal() as session:
            repo = RenderRepository(session)
            engine = RenderEngineService()

            try:
                # 1. Mark job as processing
                await repo.update_progress(job_id, progress=5, status=RenderStatus.processing)

                # 2. Fetch project scenes with assets ordered by scene_number
                query = (
                    select(Scene)
                    .where(Scene.project_id == project_id)
                    .options(selectinload(Scene.assets))
                    .order_by(Scene.scene_number.asc())
                )
                res = await session.execute(query)
                scenes = list(res.scalars().all())

                scenes_data: List[Dict[str, Any]] = []
                total_duration = 0.0

                for s in scenes:
                    dur = float(s.duration or 5.0)
                    total_duration += dur

                    # Find image asset
                    img_asset = next((a for a in s.assets if a.asset_type == AssetType.image), None)
                    image_url = img_asset.url if img_asset else ""

                    # Find audio asset
                    audio_asset = next((a for a in s.assets if a.asset_type == AssetType.audio), None)
                    audio_url = audio_asset.url if audio_asset else ""

                    cam_val = s.camera_motion.value if hasattr(s.camera_motion, "value") else str(s.camera_motion)
                    anim_val = s.animation_style.value if hasattr(s.animation_style, "value") else str(s.animation_style)

                    scenes_data.append({
                        "scene_number": s.scene_number,
                        "duration": dur,
                        "image_url": image_url,
                        "audio_url": audio_url,
                        "narration": s.narration or "",
                        "subtitle": s.subtitle or s.narration or "",
                        "camera_motion": cam_val,
                        "animation_style": anim_val,
                    })

                # Setup destination path
                output_filename = f"{job_id}.mp4"
                output_path = os.path.join(settings.video_storage_dir, output_filename)

                # Progress callback updater
                async def on_progress(percentage: int, message: str):
                    await repo.update_progress(job_id, progress=percentage)

                # 3. Run render engine compilation
                await engine.compile_video(
                    scenes_data=scenes_data,
                    output_path=output_path,
                    progress_callback=on_progress
                )

                # 4. Validate output file on disk
                if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                    raise RuntimeError("Rendered video file does not exist or has 0 bytes.")

                file_size = os.path.getsize(output_path)
                final_video_url = f"/api/v1/render/video/{job_id}"

                # 5. Create Video & Export records in DB
                await repo.create_video_and_export(
                    project_id=project_id,
                    user_id=user_id,
                    job_id=job_id,
                    video_url=final_video_url,
                    duration=max(total_duration, 3.0),
                    file_size=file_size
                )

                # 6. Update job to completed
                await repo.update_progress(job_id, progress=100, status=RenderStatus.completed)
                logger.info(f"Render job {job_id} successfully completed. Output: {output_path} ({file_size} bytes)")

            except Exception as exc:
                logger.exception(f"Render job {job_id} failed: {exc}")
                safe_error = "Video rendering failed during encoding. Please try again."
                msg = str(exc)
                if not any(secret in msg.lower() for secret in ["key", "token", "secret", "password"]):
                    safe_error = msg[:200]
                await repo.update_progress(
                    job_id,
                    progress=0,
                    status=RenderStatus.failed,
                    error_message=safe_error
                )

    async def get_job_status(self, job_id: UUID, user_id_str: Optional[str] = None) -> RenderJobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")
        if user_id_str is not None:
            user_uuid = UUID(str(user_id_str))
            if job.user_id != user_uuid:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")

        resp = RenderJobResponse.model_validate(job)
        video = await self.repo.get_video_by_job(job.id)
        if video:
            resp.video_url = video.url
        return resp
