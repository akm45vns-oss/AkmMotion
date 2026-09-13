from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from app.core.dependencies import get_db, get_current_user_id
from app.models.models import Project, Video, RenderJob


class AnalyticsResponseSchema(BaseModel):
    projects_count: int
    videos_count: int
    total_render_seconds: float
    storage_used_mb: float
    credits_remaining: int


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponseSchema)
async def get_analytics(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_id = UUID(current_user_id)

    # Projects count
    proj_query = select(func.count(Project.id)).where(Project.user_id == user_id)
    proj_res = await db.execute(proj_query)
    projects_count = proj_res.scalar_one()

    # Videos count
    vid_query = select(func.count(Video.id)).join(Project).where(Project.user_id == user_id)
    vid_res = await db.execute(vid_query)
    videos_count = vid_res.scalar_one()

    # Total duration
    dur_query = select(func.sum(Video.duration)).join(Project).where(Project.user_id == user_id)
    dur_res = await db.execute(dur_query)
    total_dur = dur_res.scalar_one() or 0.0

    return AnalyticsResponseSchema(
        projects_count=projects_count,
        videos_count=videos_count,
        total_render_seconds=round(total_dur, 1),
        storage_used_mb=round(videos_count * 15.5, 1),
        credits_remaining=100
    )
