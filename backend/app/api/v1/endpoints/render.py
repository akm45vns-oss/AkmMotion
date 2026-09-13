from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.render import RenderJobResponse
from app.services.render_service import RenderService

router = APIRouter(prefix="/render", tags=["Render Pipeline"])


@router.post("/start/{project_id}", response_model=RenderJobResponse, status_code=status.HTTP_201_CREATED)
async def start_render(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = RenderService(db)
    return await service.start_render_job(project_id, current_user_id)


@router.get("/status/{job_id}", response_model=RenderJobResponse)
async def get_render_status(
    job_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = RenderService(db)
    return await service.get_job_status(job_id, current_user_id)
