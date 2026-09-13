import os
from uuid import UUID
from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user_id
from app.core.config import settings
from app.repositories.render_repo import RenderRepository
from app.models.models import RenderStatus
from app.schemas.render import RenderJobResponse
from app.services.render_service import RenderService

router = APIRouter(prefix="/render", tags=["Render Pipeline"])


@router.post("/start/{project_id}", response_model=RenderJobResponse, status_code=status.HTTP_201_CREATED)
async def start_render(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = RenderService(db)
    return await service.start_render_job(project_id, current_user_id, background_tasks=background_tasks)


@router.get("/status/{job_id}", response_model=RenderJobResponse)
async def get_render_status(
    job_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = RenderService(db)
    return await service.get_job_status(job_id, current_user_id)


@router.get("/video/{job_id}")
async def get_render_video(
    job_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Streams and downloads the rendered MP4 video with strict IDOR ownership verification.
    Supports HTTP Range requests for in-browser seeking and playback.
    """
    repo = RenderRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")

    user_uuid = UUID(str(current_user_id))
    if job.user_id != user_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render job not found")

    if job.status != RenderStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video is not ready yet (current status: {job.status.value})"
        )

    # Resolve video file path
    possible_paths = [
        os.path.join(settings.video_storage_dir, f"{job_id}.mp4"),
        os.path.join(settings.video_storage_dir, f"render_{job_id}.mp4"),
    ]
    video = await repo.get_video_by_job(job_id)
    if video and video.storage_path:
        possible_paths.insert(0, os.path.join(settings.video_storage_dir, os.path.basename(video.storage_path)))
        if os.path.isfile(video.storage_path):
            possible_paths.insert(0, video.storage_path)

    real_path = next((p for p in possible_paths if os.path.isfile(p) and os.path.getsize(p) > 0), None)
    if not real_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk")

    filename = f"akmmotion_{str(job.project_id)[:8]}.mp4"
    return FileResponse(
        path=real_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )
