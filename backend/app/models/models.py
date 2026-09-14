import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, BigInteger, Boolean, DateTime,
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

# Enums
class AuthProvider(str, enum.Enum):
    email = "email"
    google = "google"

class ProjectStatus(str, enum.Enum):
    draft = "draft"
    analyzing = "analyzing"
    generating = "generating"
    completed = "completed"
    failed = "failed"

class ScriptStatus(str, enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    analyzed = "analyzed"
    failed = "failed"

class SceneStatus(str, enum.Enum):
    pending = "pending"
    generating = "generating"
    ready = "ready"
    failed = "failed"

class AnimationStyle(str, enum.Enum):
    zoom = "zoom"
    pan = "pan"
    fade = "fade"
    slide = "slide"
    parallax = "parallax"
    ken_burns = "ken_burns"
    motion_blur = "motion_blur"
    camera_push = "camera_push"
    camera_pull = "camera_pull"
    rotate = "rotate"

class TransitionType(str, enum.Enum):
    cut = "cut"
    fade = "fade"
    slide = "slide"
    wipe = "wipe"
    zoom = "zoom"

class CameraMotion(str, enum.Enum):
    push = "push"
    pull = "pull"
    static = "static"
    pan_left = "pan_left"
    pan_right = "pan_right"
    tilt_up = "tilt_up"
    tilt_down = "tilt_down"

class AssetType(str, enum.Enum):
    image = "image"
    audio = "audio"
    video = "video"
    subtitle = "subtitle"

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    child = "child"

class RenderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class ImageProvider(str, enum.Enum):
    dalle = "dalle"
    sdxl = "sdxl"
    midjourney = "midjourney"

class AudioType(str, enum.Enum):
    narration = "narration"
    music = "music"
    sfx = "sfx"

class ThemeMode(str, enum.Enum):
    dark = "dark"
    light = "light"
    system = "system"

class VideoQuality(str, enum.Enum):
    res_720p = "720p"
    res_1080p = "1080p"

class ExportFormat(str, enum.Enum):
    mp4 = "mp4"
    webm = "webm"


# Helper function to generate enum Column definitions with PostgreSQL type mapping
def pg_enum(enum_cls, name: str, default=None):
    return SQLEnum(
        enum_cls,
        name=name,
        values_callable=lambda x: [e.value for e in x],
        create_type=False
    )


# 1. User
class User(Base):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    auth_provider = Column(pg_enum(AuthProvider, "user_auth_provider"), nullable=False, default=AuthProvider.email)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


# 2. Project
class Project(Base):
    __tablename__ = "projects"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    style = Column(String(100), nullable=False, default="Explainer")
    language = Column(String(10), nullable=False, default="en")
    status = Column(pg_enum(ProjectStatus, "project_status"), nullable=False, default=ProjectStatus.draft)
    thumbnail_url = Column(Text, nullable=True)

    user = relationship("User", back_populates="projects")
    script = relationship("Script", back_populates="project", uselist=False, cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="project", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")


# 3. Script
class Script(Base):
    __tablename__ = "scripts"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=True)
    estimated_duration = Column(Float, nullable=True)
    language = Column(String(10), nullable=False, default="en")
    status = Column(pg_enum(ScriptStatus, "script_status"), nullable=False, default=ScriptStatus.pending)
    analysis_result = Column(JSONB, nullable=True)

    project = relationship("Project", back_populates="script")
    scenes = relationship("Scene", back_populates="script", cascade="all, delete-orphan")


# 4. Scene
class Scene(Base):
    __tablename__ = "scenes"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_number = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False, default=5.0)
    narration = Column(Text, nullable=False)
    subtitle = Column(Text, nullable=False)
    image_prompt = Column(Text, nullable=False)
    animation_style = Column(pg_enum(AnimationStyle, "animation_style_type"), nullable=False, default=AnimationStyle.ken_burns)
    transition = Column(pg_enum(TransitionType, "transition_type"), nullable=False, default=TransitionType.fade)
    camera_motion = Column(pg_enum(CameraMotion, "camera_motion_type"), nullable=False, default=CameraMotion.push)
    emotion = Column(String(100), nullable=True)
    background_music = Column(String(255), nullable=True)
    sound_effects = Column(JSONB, nullable=True)
    status = Column(pg_enum(SceneStatus, "scene_status"), nullable=False, default=SceneStatus.pending)

    project = relationship("Project", back_populates="scenes")
    script = relationship("Script", back_populates="scenes")
    assets = relationship("SceneAsset", back_populates="scene", cascade="all, delete-orphan")


# 5. SceneAsset
class SceneAsset(Base):
    __tablename__ = "scene_assets"

    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(pg_enum(AssetType, "asset_type_enum"), nullable=False)
    url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    metadata_json = Column("metadata", JSONB, nullable=True)

    scene = relationship("Scene", back_populates="assets")





# 8. RenderJob
class RenderJob(Base):
    __tablename__ = "render_jobs"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(pg_enum(RenderStatus, "render_status"), nullable=False, default=RenderStatus.pending)
    progress = Column(Integer, nullable=False, default=0)
    celery_task_id = Column(String(255), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    estimated_seconds = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    project = relationship("Project", back_populates="render_jobs")


# 9. Video
class Video(Base):
    __tablename__ = "videos"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    render_job_id = Column(UUID(as_uuid=True), ForeignKey("render_jobs.id", ondelete="SET NULL"), nullable=True)
    url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    duration = Column(Float, nullable=False)
    width = Column(Integer, nullable=False, default=1080)
    height = Column(Integer, nullable=False, default=1920)
    file_size = Column(BigInteger, nullable=False, default=0)
    format = Column(String(10), nullable=False, default="mp4")

    project = relationship("Project", back_populates="videos")


# 10. Image
class Image(Base):
    __tablename__ = "images"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    style = Column(String(100), nullable=False, default="realistic")
    provider = Column(pg_enum(ImageProvider, "image_provider_enum"), nullable=False, default=ImageProvider.dalle)


# 11. Audio
class Audio(Base):
    __tablename__ = "audio"

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True, index=True)
    audio_type = Column(pg_enum(AudioType, "audio_type_enum"), nullable=False, default=AudioType.narration)
    url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    duration = Column(Float, nullable=False, default=0.0)


# 12. UserSettings
class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(pg_enum(ThemeMode, "theme_enum"), nullable=False, default=ThemeMode.dark)
    language = Column(String(10), nullable=False, default="en")
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    export_defaults = Column(JSONB, nullable=True, default={})
    video_quality = Column(pg_enum(VideoQuality, "video_quality_enum"), nullable=False, default=VideoQuality.res_1080p)

    user = relationship("User", back_populates="settings")





# 16. Export
class Export(Base):
    __tablename__ = "exports"

    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(pg_enum(ExportFormat, "export_format_enum"), nullable=False, default=ExportFormat.mp4)
    quality = Column(pg_enum(VideoQuality, "video_quality_enum"), nullable=False, default=VideoQuality.res_1080p)
    url = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    download_count = Column(Integer, nullable=False, default=0)





# 18. Character (CME canonical model)
from app.models.character import DBCharacter as Character

