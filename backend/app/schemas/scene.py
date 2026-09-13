from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.models import SceneStatus, AnimationStyle, TransitionType, CameraMotion, AssetType


class SceneAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scene_id: UUID
    asset_type: AssetType
    url: str
    storage_path: str
    metadata_json: Optional[Any] = None


class SceneBase(BaseModel):
    scene_number: int
    duration: float = 5.0
    narration: str
    subtitle: str
    image_prompt: str
    animation_style: AnimationStyle = AnimationStyle.ken_burns
    transition: TransitionType = TransitionType.fade
    camera_motion: CameraMotion = CameraMotion.push
    emotion: Optional[str] = None
    background_music: Optional[str] = None


class SceneCreate(SceneBase):
    project_id: UUID
    script_id: UUID


class SceneUpdate(BaseModel):
    narration: Optional[str] = None
    subtitle: Optional[str] = None
    image_prompt: Optional[str] = None
    duration: Optional[float] = None
    animation_style: Optional[AnimationStyle] = None
    transition: Optional[TransitionType] = None
    camera_motion: Optional[CameraMotion] = None
    emotion: Optional[str] = None


class SceneResponse(SceneBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    script_id: UUID
    status: SceneStatus
    created_at: datetime
    updated_at: datetime
    assets: List[SceneAssetResponse] = []

    @classmethod
    def from_scene(cls, scene):
        asset_list = []
        try:
            if hasattr(scene, 'assets') and scene.assets:
                asset_list = [SceneAssetResponse.model_validate(a) for a in scene.assets]
        except Exception:
            asset_list = []

        return cls(
            id=scene.id,
            project_id=scene.project_id,
            script_id=scene.script_id,
            scene_number=scene.scene_number,
            duration=scene.duration,
            narration=scene.narration,
            subtitle=scene.subtitle,
            image_prompt=scene.image_prompt,
            animation_style=scene.animation_style,
            transition=scene.transition,
            camera_motion=scene.camera_motion,
            emotion=scene.emotion,
            background_music=scene.background_music,
            status=scene.status,
            created_at=scene.created_at,
            updated_at=scene.updated_at,
            assets=asset_list
        )


class SceneReorderItem(BaseModel):
    scene_id: UUID
    scene_number: int


class SceneReorderRequest(BaseModel):
    items: List[SceneReorderItem]
