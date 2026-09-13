from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.models.models import Project, Script, ScriptStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: UUID, user_id: Optional[UUID] = None) -> Optional[Project]:
        if user_id:
            query = (
                select(Project)
                .where(Project.id == project_id, Project.user_id == user_id)
                .options(selectinload(Project.script))
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        return None

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Project], int]:
        count_query = select(func.count(Project.id)).where(Project.user_id == user_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = (
            select(Project)
            .where(Project.user_id == user_id)
            .options(selectinload(Project.script))
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create(
        self, user_id: UUID, title: str, description: Optional[str], style: str, language: str, script_content: Optional[str]
    ) -> Project:
        project = Project(
            user_id=user_id,
            title=title,
            description=description,
            style=style,
            language=language
        )
        self.db.add(project)
        await self.db.flush()

        if script_content:
            word_count = len(script_content.split())
            estimated_duration = round(word_count / 2.5, 1)  # ~150 words per min = 2.5 words/sec

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