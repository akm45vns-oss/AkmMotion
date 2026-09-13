from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.models import Scene, Project


class SceneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, scene_id: UUID, user_id: Optional[UUID] = None) -> Optional[Scene]:
        if user_id:
            query = (
                select(Scene)
                .join(Project, Scene.project_id == Project.id)
                .where(Scene.id == scene_id, Project.user_id == user_id)
                .options(selectinload(Scene.assets))
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        return None

    async def get_by_project(self, project_id: UUID, user_id: Optional[UUID] = None) -> List[Scene]:
        if user_id:
            query = (
                select(Scene)
                .join(Project, Scene.project_id == Project.id)
                .where(Scene.project_id == project_id, Project.user_id == user_id)
                .options(selectinload(Scene.assets))
                .order_by(Scene.scene_number.asc())
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        return []

    async def update(self, scene: Scene) -> Scene:
        await self.db.commit()
        await self.db.refresh(scene)
        return scene

    async def delete(self, scene: Scene) -> None:
        await self.db.delete(scene)
        await self.db.commit()

    async def reorder(self, items: List[tuple[UUID, int]], user_id: Optional[UUID] = None) -> None:
        for scene_id, new_number in items:
            scene = await self.get_by_id(scene_id, user_id)
            if scene:
                scene.scene_number = new_number
        await self.db.commit()