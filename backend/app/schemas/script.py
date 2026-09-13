from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.models import ScriptStatus


class ScriptBase(BaseModel):
    content: str
    language: str = "en"


class ScriptCreate(ScriptBase):
    project_id: UUID


class ScriptUpdate(BaseModel):
    content: Optional[str] = None
    language: Optional[str] = None


class ScriptResponse(ScriptBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    word_count: Optional[int] = None
    estimated_duration: Optional[float] = None
    status: ScriptStatus
    analysis_result: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
