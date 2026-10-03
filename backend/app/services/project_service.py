from uuid import UUID
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse


def parse_user_uuid(user_id_str: str) -> UUID:
    try:
        return UUID(str(user_id_str))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier"
        )


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def get_project(self, project_id: UUID, user_id_str: str) -> ProjectResponse:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.get_by_id_raw(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )
        if project.user_id != user_uuid:
            if not project.workspace_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied.")
            from app.core.dependencies import verify_workspace_access
            has_access = await verify_workspace_access(project.workspace_id, user_uuid, "viewer", self.repo.db)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to workspace denied.")
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
        from app.core.dependencies import ensure_user_in_db
        await ensure_user_in_db(self.repo.db, user_uuid)

        # If creating within a workspace, verify editor permissions
        if data.workspace_id:
            from app.core.dependencies import verify_workspace_access
            has_access = await verify_workspace_access(data.workspace_id, user_uuid, "editor", self.repo.db)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor permissions required to create project in workspace.")

        project = await self.repo.create(
            user_id=user_uuid,
            title=data.title,
            description=data.description,
            style=data.style,
            language=data.language,
            script_content=data.script_content,
            workspace_id=data.workspace_id
        )
        # Re-fetch with eager-loaded script to avoid async lazy-load crash
        project = await self.repo.get_by_id_raw(project.id)
        return ProjectResponse.from_project(project)

    async def update_project(self, project_id: UUID, data: ProjectUpdate, user_id_str: str) -> ProjectResponse:
        user_uuid = parse_user_uuid(user_id_str)
        project = await self.repo.get_by_id_raw(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )

        if project.user_id != user_uuid:
            if not project.workspace_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied.")
            from app.core.dependencies import verify_workspace_access
            has_access = await verify_workspace_access(project.workspace_id, user_uuid, "editor", self.repo.db)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor permissions required to update project.")

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
        project = await self.repo.get_by_id_raw(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied."
            )

        if project.user_id != user_uuid:
            if not project.workspace_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied.")
            from app.core.dependencies import verify_workspace_access
            has_access = await verify_workspace_access(project.workspace_id, user_uuid, "admin", self.repo.db)
            if not has_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required to delete project.")

        await self.repo.delete(project)