from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.models import Scene, Project


class SceneRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, scene_id: UUID) -> Optional[Scene]:
        query = (
            select(Scene)
            .where(Scene.id == scene_id)
            .options(selectinload(Scene.assets))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: UUID, user_id: Optional[UUID] = None) -> List[Scene]:
        query = (
            select(Scene)
            .where(Scene.project_id == project_id)
            .options(selectinload(Scene.assets))
            .order_by(Scene.scene_number.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, scene: Scene) -> Scene:
        await self.db.commit()
        await self.db.refresh(scene)
        return scene

    async def delete(self, scene: Scene) -> None:
        await self.db.delete(scene)
        await self.db.commit()

    async def reorder(self, items: List[tuple[UUID, int]]) -> None:
        for scene_id, new_number in items:
            scene = await self.get_by_id(scene_id)
            if scene:
                scene.scene_number = new_number
        await self.db.commit()