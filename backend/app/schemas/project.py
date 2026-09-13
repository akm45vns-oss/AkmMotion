from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.models import ProjectStatus
from app.schemas.script import ScriptResponse


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    style: str = "Explainer"
    language: str = "en"


class ProjectCreate(ProjectBase):
    script_content: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    style: Optional[str] = None
    language: Optional[str] = None
    status: Optional[ProjectStatus] = None
    thumbnail_url: Optional[str] = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: ProjectStatus
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    script: Optional[ScriptResponse] = None

    @classmethod
    def from_project(cls, project):
        script_resp = None
        # Safely check __dict__ to avoid triggering async lazy load MissingGreenlet
        if "script" in project.__dict__ and project.__dict__["script"] is not None:
            try:
                script_resp = ScriptResponse.model_validate(project.__dict__["script"])
            except Exception:
                script_resp = None

        return cls(
            id=project.id,
            user_id=project.user_id,
            title=project.title,
            description=project.description,
            style=project.style,
            language=project.language,
            status=project.status,
            thumbnail_url=project.thumbnail_url,
            created_at=project.created_at,
            updated_at=project.updated_at,
            script=script_resp
        )


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    limit: int