-- AkmMotion Neon PostgreSQL Production Schema DDL
-- Complete 18-Table Schema with Indexes, Foreign Keys, and Constraints

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum Types
CREATE TYPE user_auth_provider AS ENUM ('email', 'google');
CREATE TYPE project_status AS ENUM ('draft', 'analyzing', 'generating', 'completed', 'failed');
CREATE TYPE script_status AS ENUM ('pending', 'analyzing', 'analyzed', 'failed');
CREATE TYPE scene_status AS ENUM ('pending', 'generating', 'ready', 'failed');
CREATE TYPE animation_style_type AS ENUM ('zoom', 'pan', 'fade', 'slide', 'parallax', 'ken_burns', 'motion_blur', 'camera_push', 'camera_pull', 'rotate');
CREATE TYPE transition_type AS ENUM ('cut', 'fade', 'slide', 'wipe', 'zoom');
CREATE TYPE camera_motion_type AS ENUM ('push', 'pull', 'static', 'pan_left', 'pan_right', 'tilt_up', 'tilt_down');
CREATE TYPE asset_type_enum AS ENUM ('image', 'audio', 'video', 'subtitle');
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'child');
CREATE TYPE render_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
CREATE TYPE image_provider_enum AS ENUM ('dalle', 'sdxl', 'midjourney');
CREATE TYPE audio_type_enum AS ENUM ('narration', 'music', 'sfx');
CREATE TYPE theme_enum AS ENUM ('dark', 'light', 'system');
CREATE TYPE video_quality_enum AS ENUM ('720p', '1080p');
CREATE TYPE export_format_enum AS ENUM ('mp4', 'webm');

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    auth_provider user_auth_provider NOT NULL DEFAULT 'email',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    style VARCHAR(100) NOT NULL DEFAULT 'Explainer',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    status project_status NOT NULL DEFAULT 'draft',
    thumbnail_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- 3. scripts
CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    word_count INTEGER,
    estimated_duration FLOAT,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    status script_status NOT NULL DEFAULT 'pending',
    analysis_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scripts_project_id ON scripts(project_id);

-- 4. scenes
CREATE TABLE IF NOT EXISTS scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES scripts(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    duration FLOAT NOT NULL DEFAULT 5.0,
    narration TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    image_prompt TEXT NOT NULL,
    animation_style animation_style_type NOT NULL DEFAULT 'ken_burns',
    transition transition_type NOT NULL DEFAULT 'fade',
    camera_motion camera_motion_type NOT NULL DEFAULT 'push',
    emotion VARCHAR(100),
    background_music VARCHAR(255),
    sound_effects JSONB,
    status scene_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scenes_project_id ON scenes(project_id);

-- 5. scene_assets
CREATE TABLE IF NOT EXISTS scene_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    asset_type asset_type_enum NOT NULL,
    url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scene_assets_scene_id ON scene_assets(scene_id);



-- 8. render_jobs
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status render_status NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    celery_task_id VARCHAR(255),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    estimated_seconds INTEGER,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_render_jobs_project_id ON render_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_user_id ON render_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_celery_task ON render_jobs(celery_task_id);

-- 9. videos
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    render_job_id UUID REFERENCES render_jobs(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    duration FLOAT NOT NULL,
    width INTEGER NOT NULL DEFAULT 1080,
    height INTEGER NOT NULL DEFAULT 1920,
    file_size BIGINT NOT NULL DEFAULT 0,
    format VARCHAR(10) NOT NULL DEFAULT 'mp4',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_videos_project_id ON videos(project_id);

-- 10. images
CREATE TABLE IF NOT EXISTS images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scene_id UUID REFERENCES scenes(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    prompt TEXT NOT NULL,
    style VARCHAR(100) NOT NULL DEFAULT 'realistic',
    provider image_provider_enum NOT NULL DEFAULT 'dalle',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_images_project_id ON images(project_id);

-- 11. audio
CREATE TABLE IF NOT EXISTS audio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scene_id UUID REFERENCES scenes(id) ON DELETE SET NULL,
    audio_type audio_type_enum NOT NULL DEFAULT 'narration',
    url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    duration FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audio_project_id ON audio(project_id);

-- 12. user_settings
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme theme_enum NOT NULL DEFAULT 'dark',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    notifications_enabled BOOLEAN NOT NULL DEFAULT true,
    export_defaults JSONB DEFAULT '{}'::jsonb,
    video_quality video_quality_enum NOT NULL DEFAULT '1080p',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);



-- 16. exports
CREATE TABLE IF NOT EXISTS exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    format export_format_enum NOT NULL DEFAULT 'mp4',
    quality video_quality_enum NOT NULL DEFAULT '1080p',
    url TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    download_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_exports_user_id ON exports(user_id);



-- 18. characters
CREATE TABLE IF NOT EXISTS characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar_url TEXT,
    style_prompt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);

-- 19. character_profiles
CREATE TABLE IF NOT EXISTS character_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    role VARCHAR(64) DEFAULT 'Protagonist' NOT NULL,
    age INTEGER DEFAULT 25 NOT NULL,
    gender VARCHAR(32) DEFAULT 'Male' NOT NULL,
    ethnicity VARCHAR(64),
    summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_character_profiles_char_id ON character_profiles(character_id);

-- 20. character_dna
CREATE TABLE IF NOT EXISTS character_dna (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    skin_tone VARCHAR(64) DEFAULT 'Medium',
    hair_color VARCHAR(64) DEFAULT 'Black',
    hair_style VARCHAR(64) DEFAULT 'Short neat',
    hair_length VARCHAR(64) DEFAULT 'Short',
    eye_color VARCHAR(64) DEFAULT 'Brown',
    face_shape VARCHAR(64) DEFAULT 'Oval',
    beard VARCHAR(64),
    mustache VARCHAR(64),
    body_type VARCHAR(64) DEFAULT 'Average',
    height_category VARCHAR(64) DEFAULT 'Medium',
    outfit VARCHAR(255) DEFAULT 'Casual blue hoodie and black jeans',
    shoes VARCHAR(128) DEFAULT 'White sneakers',
    expression VARCHAR(128) DEFAULT 'Friendly smile',
    visual_style VARCHAR(128) DEFAULT 'Pixar 3D Render',
    lighting_preference VARCHAR(128) DEFAULT 'Cinematic golden hour light',
    camera_preference VARCHAR(128) DEFAULT 'Medium eye-level shot',
    prompt_prefix TEXT DEFAULT 'Masterpiece 9:16 vertical 8k render',
    prompt_suffix TEXT DEFAULT 'same facial features, same clothes, consistent identity',
    negative_prompt TEXT DEFAULT 'deformed face, wrong clothes, inconsistent character',
    consistency_strength FLOAT DEFAULT 0.95,
    attributes_json JSONB
);
CREATE INDEX IF NOT EXISTS idx_character_dna_char_id ON character_dna(character_id);

-- 21. character_embeddings
CREATE TABLE IF NOT EXISTS character_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    embedding_type VARCHAR(64) DEFAULT 'face',
    vector_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 22. character_styles
CREATE TABLE IF NOT EXISTS character_styles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    style_name VARCHAR(64) NOT NULL,
    prompt_modifier TEXT NOT NULL
);

-- 23. character_outfits
CREATE TABLE IF NOT EXISTS character_outfits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    outfit_name VARCHAR(64) NOT NULL,
    description TEXT NOT NULL
);

-- 24. character_accessories
CREATE TABLE IF NOT EXISTS character_accessories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    accessory_name VARCHAR(64) NOT NULL
);

-- 25. character_relationships
CREATE TABLE IF NOT EXISTS character_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    related_character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    relationship_type VARCHAR(64) NOT NULL
);

-- 26. character_reference_images
CREATE TABLE IF NOT EXISTS character_reference_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 27. character_scene_assignments
CREATE TABLE IF NOT EXISTS character_scene_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE
);

-- 28. character_versions
CREATE TABLE IF NOT EXISTS character_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    dna_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
