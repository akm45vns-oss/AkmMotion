-- AkmMotion Supabase PostgreSQL Schema DDL
-- Complete 18-Table Production Schema with RLS and Indexes

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
CREATE TYPE voice_provider_enum AS ENUM ('elevenlabs', 'openai', 'google');
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'child');
CREATE TYPE voice_style_enum AS ENUM ('narrator', 'calm', 'energetic', 'professional', 'storytelling');
CREATE TYPE render_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
CREATE TYPE image_provider_enum AS ENUM ('dalle', 'sdxl', 'midjourney');
CREATE TYPE audio_type_enum AS ENUM ('narration', 'music', 'sfx');
CREATE TYPE theme_enum AS ENUM ('dark', 'light', 'system');
CREATE TYPE video_quality_enum AS ENUM ('720p', '1080p', '4k');
CREATE TYPE sub_plan_enum AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE sub_status_enum AS ENUM ('active', 'cancelled', 'past_due', 'trialing');
CREATE TYPE credit_tx_type AS ENUM ('purchase', 'usage', 'refund', 'bonus');
CREATE TYPE notification_type_enum AS ENUM ('render_started', 'render_complete', 'render_failed', 'export_complete');
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

-- 6. voices
CREATE TABLE IF NOT EXISTS voices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider voice_provider_enum NOT NULL DEFAULT 'openai',
    external_voice_id VARCHAR(255) NOT NULL,
    gender gender_enum NOT NULL DEFAULT 'male',
    style voice_style_enum NOT NULL DEFAULT 'narrator',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    preview_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. templates
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    style VARCHAR(100) NOT NULL,
    thumbnail_url TEXT,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_public BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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
    voice_id UUID REFERENCES voices(id) ON DELETE SET NULL,
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

-- 13. subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan sub_plan_enum NOT NULL DEFAULT 'free',
    status sub_status_enum NOT NULL DEFAULT 'active',
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);

-- 14. credits
CREATE TABLE IF NOT EXISTS credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type credit_tx_type NOT NULL,
    description TEXT NOT NULL,
    balance_after INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_credits_user_id ON credits(user_id);

-- 15. notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type_enum NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

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

-- 17. activity_logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);

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

-- ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE exports ENABLE ROW LEVEL SECURITY;

-- Sample RLS Policy: Users can only view/modify their own projects
CREATE POLICY user_projects_policy ON projects 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY user_settings_policy ON user_settings 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY user_render_jobs_policy ON render_jobs 
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY user_notifications_policy ON notifications 
    FOR ALL USING (auth.uid() = user_id);
