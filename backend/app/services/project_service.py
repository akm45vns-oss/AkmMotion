from uuid import UUID
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse

DEFAULT_GUEST_UUID = UUID("595744ab-c375-4bec-a3c0-429113163fe1")


def parse_user_uuid(user_id_str: str) -> UUID:
    try:
        return UUID(str(user_id_str))
    except Exception:
        return DEFAULT_GUEST_UUID


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def get_project(self, project_id: UUID, user_id_str: str) -> ProjectResponse:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.get_by_id(project_id, user_uuid)
        if not project:
            # Fallback check without user restriction
            project = await self.repo.get_by_id(project_id, None)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )
        return ProjectResponse.from_project(project)

    async def list_user_projects(self, user_id_str: str, page: int = 1, limit: int = 20) -> ProjectListResponse:
        user_uuid = parse_user_uuid(user_id_str)
        skip = (page - 1) * limit
        items, total = await self.repo.list_by_user(user_uuid, skip=skip, limit=limit)
        
        project_responses = [ProjectResponse.from_project(p) for p in items]
        return ProjectListResponse(
            items=project_responses,
            total=total,
            page=page,
            limit=limit
        )

    async def create_project(self, data: ProjectCreate, user_id_str: str) -> ProjectResponse:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.create(
            user_id=user_uuid,
            title=data.title,
            description=data.description,
            style=data.style,
            language=data.language,
            script_content=data.script_content
        )
        # Re-fetch with eager-loaded script to avoid async lazy-load crash
        project = await self.repo.get_by_id(project.id, user_uuid)
        return ProjectResponse.from_project(project)

    async def update_project(self, project_id: UUID, data: ProjectUpdate, user_id_str: str) -> ProjectResponse:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.get_by_id(project_id, user_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )

        if data.title is not None:
            project.title = data.title
        if data.description is not None:
            project.description = data.description
        if data.style is not None:
            project.style = data.style
        if data.language is not None:
            project.language = data.language
        if data.status is not None:
            project.status = data.status
        if data.thumbnail_url is not None:
            project.thumbnail_url = data.thumbnail_url

        updated_project = await self.repo.update(project)
        return ProjectResponse.from_project(updated_project)

    async def delete_project(self, project_id: UUID, user_id_str: str) -> None:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.get_by_id(project_id, user_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )
        await self.repo.delete(project)