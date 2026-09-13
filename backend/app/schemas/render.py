from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.models import RenderStatus


class RenderJobCreate(BaseModel):
    project_id: UUID


class RenderJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    status: RenderStatus
    progress: int
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    estimated_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    render_job_id: Optional[UUID] = None
    url: str
    storage_path: str
    duration: float
    width: int
    height: int
    file_size: int
    format: str
    created_at: datetime
