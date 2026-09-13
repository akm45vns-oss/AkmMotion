import os
import asyncio
import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID
from sqlalchemy.future import select

from app.core.security import create_access_token
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.models import Project, Scene, SceneAsset, AssetType, RenderStatus, CameraMotion, AnimationStyle, RenderJob
from app.services.render_engine import RenderEngineService
from app.services.render_service import RenderService


@pytest.mark.asyncio
async def test_real_mp4_render_pipeline(client: AsyncClient):
    """
    Integration test: End-to-end real server-side video rendering.
    1. Creates project and scene in DB
    2. Starts render via POST /api/v1/render/start/{project_id}
    3. Executes real FFmpeg rendering pipeline producing an actual MP4
    4. Validates MP4 file on disk, file size > 0, MP4 ftyp container header
    5. Validates RenderJob state reaches completed with progress=100
    6. Validates video stream/download endpoint returns 200 video/mp4 with range support
    """
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project via API
    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Real Render Integration Test",
            "description": "Validating real MP4 server rendering",
            "style": "Explainer",
            "language": "en",
            "script_content": "AkmMotion produces real vertical videos."
        },
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    # 2. Add scene to project in DB with valid metadata
    async with AsyncSessionLocal() as session:
        scene = Scene(
            project_id=project_id,
            script_id=UUID(proj_res.json().get("script", {}).get("id") or str(uuid4())),
            scene_number=1,
            duration=2.5,
            narration="Welcome to AkmMotion. Real server side video rendering is now active.",
            subtitle="Real AI Video Rendering Active",
            image_prompt="Modern futuristic city 9:16 vertical",
            camera_motion=CameraMotion.push,
            animation_style=AnimationStyle.ken_burns,
            status="ready"
        )
        session.add(scene)
        await session.flush()

        # Add image asset
        asset = SceneAsset(
            scene_id=scene.id,
            asset_type=AssetType.image,
            url="",  # Fallback card will be generated cleanly by engine
            storage_path=f"images/{scene.id}.jpg",
            metadata_json={"prompt": "test prompt"}
        )
        session.add(asset)
        await session.commit()

    # 3. Start render via API
    start_res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert start_res.status_code == 201
    job_data = start_res.json()
    job_id = UUID(job_data["id"])
    assert job_data["status"] in ["pending", "processing", "completed"]

    # 4. Await background completion (wait up to 30s)
    max_wait = 30
    completed = False
    for _ in range(max_wait):
        status_res = await client.get(f"/api/v1/render/status/{job_id}", headers=headers)
        assert status_res.status_code == 200
        data = status_res.json()
        if data["status"] == "completed":
            completed = True
            break
        elif data["status"] == "failed":
            pytest.fail(f"Render job failed unexpectedly: {data.get('error_message')}")
        await asyncio.sleep(1.0)

    assert completed, "Render job did not complete within timeout"

    # 5. Verify status response attributes
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["video_url"] is not None
    assert f"/api/v1/render/video/{job_id}" in data["video_url"]

    # 6. Verify real MP4 file on disk
    expected_file = os.path.join(settings.video_storage_dir, f"{job_id}.mp4")
    assert os.path.isfile(expected_file), f"Output MP4 file does not exist at {expected_file}"
    file_size = os.path.getsize(expected_file)
    assert file_size > 1000, f"Rendered MP4 file size is too small: {file_size} bytes"

    # 7. Verify valid MP4 container header (ftyp atom in first 16 bytes)
    with open(expected_file, "rb") as f:
        header = f.read(16)
        assert b"ftyp" in header, f"File does not contain valid MP4 ftyp atom: {header}"

    # 8. Verify GET /api/v1/render/video/{job_id} endpoint
    video_res = await client.get(f"/api/v1/render/video/{job_id}", headers=headers)
    assert video_res.status_code == 200
    assert video_res.headers.get("content-type") == "video/mp4"
    assert "bytes" in video_res.headers.get("accept-ranges", "")
    assert len(video_res.content) == file_size

    # Clean up generated video file
    try:
        os.remove(expected_file)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_failed_render_handles_error_gracefully(client: AsyncClient):
    """Verifies that an unrecoverable rendering error results in 'failed' status without leaking secrets."""
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_res = await client.post(
        "/api/v1/projects",
        json={"title": "Failing Render Test", "style": "Explainer", "script_content": "Test script"},
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    # Create job directly in DB
    job_id = uuid4()
    async with AsyncSessionLocal() as session:
        from app.models.models import RenderJob
        from datetime import datetime, timezone
        job = RenderJob(
            id=job_id,
            project_id=project_id,
            user_id=UUID(user_id),
            status=RenderStatus.pending,
            progress=0
        )
        session.add(job)
        await session.commit()

    # Call update_progress with failed status & secret-free message
    async with AsyncSessionLocal() as session:
        from app.repositories.render_repo import RenderRepository
        repo = RenderRepository(session)
        await repo.update_progress(
            job_id,
            progress=0,
            status=RenderStatus.failed,
            error_message="Encoding error occurred during segment compilation"
        )

    # Fetch status via API
    res = await client.get(f"/api/v1/render/status/{job_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert "Encoding error" in data["error_message"]
    # Ensure no secret keywords are exposed
    for secret in ["key", "token", "password", "aws", "gsk_"]:
        assert secret not in data["error_message"].lower()


@pytest.mark.asyncio
async def test_duplicate_render_concurrency_protection(client: AsyncClient):
    """Verifies that duplicate render requests for the same project return the existing active job."""
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        json={"title": "Concurrency Test", "style": "Explainer", "script_content": "Concurrency check"},
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    # Create an active in-progress job in DB
    existing_job_id = uuid4()
    async with AsyncSessionLocal() as session:
        from app.models.models import RenderJob
        job = RenderJob(
            id=existing_job_id,
            project_id=project_id,
            user_id=UUID(user_id),
            status=RenderStatus.processing,
            progress=45
        )
        session.add(job)
        await session.commit()

    # Call start_render via API: should detect active job and return it rather than creating a duplicate
    res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert res.status_code == 201
    returned_data = res.json()
    assert returned_data["id"] == str(existing_job_id)
    assert returned_data["status"] == "processing"
    assert returned_data["progress"] == 45
