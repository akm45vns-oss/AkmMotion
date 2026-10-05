from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.models import AuthProvider, ThemeMode, VideoQuality


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    theme: ThemeMode
    language: str
    notifications_enabled: bool
    video_quality: VideoQuality


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters password")
    full_name: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    settings: Optional[UserSettingsResponse] = None

    @classmethod
    def from_user(cls, user):
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=getattr(user, "avatar_url", None),
            auth_provider=user.auth_provider,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=getattr(user, "created_at", None) or now,
            updated_at=getattr(user, "updated_at", None) or now,
            settings=None
        )


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
