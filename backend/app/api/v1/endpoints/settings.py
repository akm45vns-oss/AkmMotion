from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, ConfigDict
from app.core.dependencies import get_db, get_current_user_id
from app.models.models import UserSettings, ThemeMode, VideoQuality


class SettingsUpdateSchema(BaseModel):
    theme: ThemeMode = ThemeMode.dark
    language: str = "en"
    notifications_enabled: bool = True
    video_quality: VideoQuality = VideoQuality.res_1080p


class SettingsResponseSchema(SettingsUpdateSchema):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponseSchema)
async def get_settings(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    query = select(UserSettings).where(UserSettings.user_id == UUID(current_user_id))
    result = await db.execute(query)
    settings_obj = result.scalar_one_or_none()

    if not settings_obj:
        from app.core.dependencies import ensure_user_in_db
        await ensure_user_in_db(db, UUID(current_user_id))
        # Create default
        settings_obj = UserSettings(user_id=UUID(current_user_id))
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)

    return SettingsResponseSchema.model_validate(settings_obj)


@router.put("", response_model=SettingsResponseSchema)
async def update_settings(
    data: SettingsUpdateSchema,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    query = select(UserSettings).where(UserSettings.user_id == UUID(current_user_id))
    result = await db.execute(query)
    settings_obj = result.scalar_one_or_none()

    if not settings_obj:
        from app.core.dependencies import ensure_user_in_db
        await ensure_user_in_db(db, UUID(current_user_id))
        settings_obj = UserSettings(user_id=UUID(current_user_id))
        db.add(settings_obj)

    settings_obj.theme = data.theme
    settings_obj.language = data.language
    settings_obj.notifications_enabled = data.notifications_enabled
    settings_obj.video_quality = data.video_quality

    await db.commit()
    await db.refresh(settings_obj)
    return SettingsResponseSchema.model_validate(settings_obj)
