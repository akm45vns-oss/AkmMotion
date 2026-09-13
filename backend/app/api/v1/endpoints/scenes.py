from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.scene import SceneResponse, SceneUpdate, SceneReorderRequest
from app.repositories.scene_repo import SceneRepository

router = APIRouter(prefix="/scenes", tags=["Scenes"])


@router.get("/project/{project_id}", response_model=List[SceneResponse])
async def get_project_scenes(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = SceneRepository(db)
    scenes = await repo.get_by_project(project_id, UUID(current_user_id))
    return [SceneResponse.from_scene(s) for s in scenes]


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: UUID,
    data: SceneUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = SceneRepository(db)
    scene = await repo.get_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")

    if data.narration is not None:
        scene.narration = data.narration
    if data.subtitle is not None:
        scene.subtitle = data.subtitle
    if data.image_prompt is not None:
        scene.image_prompt = data.image_prompt
    if data.duration is not None:
        scene.duration = data.duration
    if data.animation_style is not None:
        scene.animation_style = data.animation_style
    if data.transition is not None:
        scene.transition = data.transition
    if data.camera_motion is not None:
        scene.camera_motion = data.camera_motion
    if data.emotion is not None:
        scene.emotion = data.emotion

    updated_scene = await repo.update(scene)
    return SceneResponse.from_scene(updated_scene)


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_scenes(
    req: SceneReorderRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = SceneRepository(db)
    tuples = [(item.scene_id, item.scene_number) for item in req.items]
    await repo.reorder(tuples)
    return {"message": "Scenes reordered successfully"}


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    repo = SceneRepository(db)
    scene = await repo.get_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    await repo.delete(scene)
