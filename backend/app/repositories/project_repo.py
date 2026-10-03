from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from app.models.models import Project, Script, ScriptStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_raw(self, project_id: UUID) -> Optional[Project]:
        query = (
            select(Project)
            .where(Project.id == project_id)
            .options(joinedload(Project.script))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, project_id: UUID, user_id: Optional[UUID] = None, required_role: str = "viewer"
    ) -> Optional[Project]:
        if not user_id:
            return None
        project = await self.get_by_id_raw(project_id)
        if not project:
            return None
        if project.user_id == user_id:
            return project
        if project.workspace_id:
            from app.core.dependencies import verify_workspace_access
            if await verify_workspace_access(project.workspace_id, user_id, required_role, self.db):
                return project
        return None

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Project], int]:
        query = (
            select(Project)
            .where(Project.user_id == user_id)
            .options(joinedload(Project.script))
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # If items on first page is less than limit, avoid second round-trip for count
        if skip == 0 and len(items) < limit:
            total = len(items)
        else:
            count_query = select(func.count(Project.id)).where(Project.user_id == user_id)
            total_result = await self.db.execute(count_query)
            total = total_result.scalar_one()

        return items, total

    async def create(
        self, user_id: UUID, title: str, description: Optional[str], style: str, language: str, script_content: Optional[str], workspace_id: Optional[UUID] = None
    ) -> Project:
        project = Project(
            user_id=user_id,
            workspace_id=workspace_id,
            title=title,
            description=description,
            style=style,
            language=language
        )
        self.db.add(project)
        await self.db.flush()

        if script_content:
            word_count = len(script_content.split())
            if word_count > 0:
                from app.services.ai.script_analyzer import ScriptAnalyzerService
                target_scenes, _ = ScriptAnalyzerService.calculate_scene_count(script_content)
                estimated_duration = ScriptAnalyzerService.calculate_estimated_duration(word_count, target_scenes)
            else:
                estimated_duration = 0.0

            script = Script(
                project_id=project.id,
                content=script_content,
                word_count=word_count,
                estimated_duration=estimated_duration,
                language=language,
                status=ScriptStatus.pending
            )
            self.db.add(script)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()