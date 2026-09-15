import uuid
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient, Response
from app.core.config import settings
from app.core.security import create_access_token
from app.core.rate_limit import _rate_limiter, rate_limit_video_gen
from app.models.models import (
    User, Project, Script, Scene, SceneAsset, AssetType,
    VideoGenerationJob, VideoGenerationStatus
)
from app.services.ai.fal_video_service import (
    FalVideoService, sanitize_error, fal_video_service
)
from app.db.session import AsyncSessionLocal


def test_sanitize_error_masks_secrets():
    """Verifies that API keys, Bearer tokens, and secrets are masked."""
    fake_key = "fal_abc123xyz_secret_key_456"
    raw_error = f"Error communicating with fal.ai using Key {fake_key} and Bearer header_token_999."
    cleaned = sanitize_error(raw_error)
    assert fake_key not in cleaned
    assert "[REDACTED]" in cleaned
    assert "Key [REDACTED]" in cleaned
    assert "Bearer [REDACTED]" in cleaned


@pytest.mark.asyncio
async def test_fal_service_configuration_check():
    """Verifies safe error raising when FAL_KEY is missing or provider is disabled."""
    service = FalVideoService()
    
    with patch.object(settings, "FAL_KEY", ""):
        with pytest.raises((ValueError, RuntimeError)) as exc_info:
            await service.submit_text_to_video("A cinematic shot")
        assert "API key is not configured" in str(exc_info.value) or "Failed to submit" in str(exc_info.value)

    with patch.object(settings, "FAL_KEY", "valid_mock_key"), patch.object(settings, "FAL_VIDEO_ENABLED", False):
        with pytest.raises(RuntimeError) as exc_info:
            await service.submit_text_to_video("A cinematic shot")
        assert "disabled" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fal_service_submit_text_to_video_mocked():
    """Tests queue submission without consuming user credits."""
    service = FalVideoService()
    mock_response = Response(
        status_code=200,
        json={
            "request_id": "req-12345",
            "status_url": "https://queue.fal.run/model/requests/req-12345/status",
            "response_url": "https://queue.fal.run/model/requests/req-12345"
        }
    )

    with patch.object(settings, "FAL_KEY", "mock_fal_key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await service.submit_text_to_video(
            prompt="Dramatic camera push into modern city skyline, 9:16 vertical",
            aspect_ratio="9:16",
            duration="5"
        )

        assert result["request_id"] == "req-12345"
        assert "status_url" in result
        assert "response_url" in result
        assert result["provider"] == "fal.ai"
        assert mock_post.called
        # Verify request headers contained Key auth
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Key mock_fal_key"
        assert call_kwargs["json"]["aspect_ratio"] == "9:16"


@pytest.mark.asyncio
async def test_fal_service_check_status_normalization():
    """Verifies that fal queue statuses (IN_QUEUE, IN_PROGRESS, COMPLETED, FAILED) normalize properly."""
    service = FalVideoService()

    status_mappings = [
        ("IN_QUEUE", "in_queue"),
        ("IN_PROGRESS", "in_progress"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed")
    ]

    with patch.object(settings, "FAL_KEY", "mock_fal_key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        for raw, expected in status_mappings:
            mock_get.return_value = Response(200, json={"status": raw})
            res = await service.check_status("https://queue.fal.run/status")
            assert res["status"] == expected


@pytest.mark.asyncio
async def test_fal_service_fetch_result_parsing():
    """Tests parsing video URLs from diverse fal response schemas."""
    service = FalVideoService()

    # Schema 1: {"video": {"url": "https://..."}}
    with patch.object(settings, "FAL_KEY", "mock_fal_key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Response(200, json={"video": {"url": "https://fal.media/clip1.mp4"}})
        res = await service.fetch_result("https://queue.fal.run/response")
        assert res["video_url"] == "https://fal.media/clip1.mp4"

    # Schema 2: {"video_url": "https://..."}
    with patch.object(settings, "FAL_KEY", "mock_fal_key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Response(200, json={"video_url": "https://fal.media/clip2.mp4"})
        res = await service.fetch_result("https://queue.fal.run/response")
        assert res["video_url"] == "https://fal.media/clip2.mp4"

    # Schema 3: {"videos": [{"url": "https://..."}]}
    with patch.object(settings, "FAL_KEY", "mock_fal_key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Response(200, json={"videos": [{"url": "https://fal.media/clip3.mp4"}]})
        res = await service.fetch_result("https://queue.fal.run/response")
        assert res["video_url"] == "https://fal.media/clip3.mp4"


def test_video_rate_limiting():
    """Verifies that rate_limit_video_gen enforces max 5 requests per minute."""
    _rate_limiter.reset()
    key = "test-user-rate-limit"
    # Max requests is 5
    for _ in range(5):
        assert _rate_limiter.is_allowed(key, max_requests=5, window_seconds=60) is True
    # 6th request must be denied
    assert _rate_limiter.is_allowed(key, max_requests=5, window_seconds=60) is False
    _rate_limiter.reset()


@pytest.mark.asyncio
async def test_generate_scene_video_idor_protection(client: AsyncClient):
    """Verifies that generating a video for another user's scene is blocked (IDOR protection)."""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    script_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        # Create user 1 (owner)
        u1 = User(id=user1_id, email=f"u1_{uuid.uuid4().hex[:6]}@test.com", full_name="User One")
        session.add(u1)
        # Create project belonging to user 1
        p = Project(id=project_id, user_id=user1_id, title="Protected Video Project")
        session.add(p)
        sc = Script(id=script_id, project_id=project_id, content="Authoritative script narration")
        session.add(sc)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Authoritative narration",
            subtitle="Authoritative narration",
            image_prompt="Visual scene description"
        )
        session.add(scene)
        await session.commit()

    # User 2 tries to trigger video generation for User 1's scene
    user2_token = create_access_token(subject=str(user2_id))
    response = await client.post(
        "/api/v1/ai/generate-scene-video",
        json={"scene_id": str(scene_id)},
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    # Must be 404 (or 403) to prevent resource leakage
    assert response.status_code == 404
    assert "Scene not found or unauthorized" in response.text


@pytest.mark.asyncio
async def test_generate_scene_video_duplicate_prevention(client: AsyncClient):
    """Verifies that duplicate video generation requests on the same scene return existing active job."""
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    script_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        u = User(id=user_id, email=f"u_{uuid.uuid4().hex[:6]}@test.com", full_name="Test User")
        session.add(u)
        p = Project(id=project_id, user_id=user_id, title="Dedup Video Project")
        session.add(p)
        sc = Script(id=script_id, project_id=project_id, content="Test content")
        session.add(sc)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Original narration",
            subtitle="Original narration",
            image_prompt="Original visual prompt"
        )
        session.add(scene)
        # Add existing active job
        existing_job = VideoGenerationJob(
            scene_id=scene_id,
            project_id=project_id,
            user_id=user_id,
            status=VideoGenerationStatus.in_queue.value,
            prompt="Original visual prompt",
            provider="fal.ai"
        )
        session.add(existing_job)
        await session.commit()

    token = create_access_token(subject=str(user_id))
    response = await client.post(
        "/api/v1/ai/generate-scene-video",
        json={"scene_id": str(scene_id)},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_queue"
    assert "already in progress" in data.get("message", "")


@pytest.mark.asyncio
async def test_get_video_job_status_completion_and_asset_creation(client: AsyncClient):
    """Verifies that polling a completed job creates SceneAsset(video) while keeping narration intact."""
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    job_id = uuid.uuid4()
    script_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        u = User(id=user_id, email=f"u_{uuid.uuid4().hex[:6]}@test.com", full_name="Job User")
        session.add(u)
        p = Project(id=project_id, user_id=user_id, title="Status Project")
        session.add(p)
        sc = Script(id=script_id, project_id=project_id, content="Hi Ayush")
        session.add(sc)
        scene = Scene(
            id=scene_id,
            project_id=project_id,
            script_id=script_id,
            scene_number=1,
            narration="Hi Ayush",
            subtitle="Hi Ayush",
            image_prompt="A friendly wave to Ayush"
        )
        session.add(scene)
        job = VideoGenerationJob(
            id=job_id,
            scene_id=scene_id,
            project_id=project_id,
            user_id=user_id,
            status=VideoGenerationStatus.in_progress.value,
            status_url="https://queue.fal.run/mock/status",
            response_url="https://queue.fal.run/mock/response",
            prompt="A friendly wave to Ayush"
        )
        session.add(job)
        await session.commit()

    token = create_access_token(subject=str(user_id))

    with patch.object(fal_video_service, "check_status", new_callable=AsyncMock) as mock_status, \
         patch.object(fal_video_service, "fetch_result", new_callable=AsyncMock) as mock_result:
        mock_status.return_value = {"status": "completed"}
        mock_result.return_value = {"video_url": "https://fal.media/generated_clip.mp4"}

        response = await client.get(
            f"/api/v1/ai/video-jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["video_url"] == "https://fal.media/generated_clip.mp4"

    # Verify database state: SceneAsset is created with asset_type=video
    # AND scene narration is 100% UNCHANGED ("Hi Ayush")
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        res = await session.execute(select(Scene).where(Scene.id == scene_id))
        persisted_scene = res.scalar_one()
        assert persisted_scene.narration == "Hi Ayush"
        assert persisted_scene.subtitle == "Hi Ayush"

        asset_res = await session.execute(
            select(SceneAsset).where(
                SceneAsset.scene_id == scene_id,
                SceneAsset.asset_type == AssetType.video
            )
        )
        video_asset = asset_res.scalar_one_or_none()
        assert video_asset is not None
        assert video_asset.url == "https://fal.media/generated_clip.mp4"
        assert video_asset.metadata_json["provider"] == "fal.ai"
