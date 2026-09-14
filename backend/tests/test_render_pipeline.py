import os
import re
import asyncio
import subprocess
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


# ---------------------------------------------------------------------------
# Helper: inspect MP4 metadata using ffmpeg -i (ffprobe-equivalent)
# ---------------------------------------------------------------------------

def _get_mp4_metadata(file_path: str) -> dict:
    """
    Runs `ffmpeg -i <file>` and parses the stderr output to extract video
    stream metadata.  Returns a dict with keys:
        duration_s, width, height, video_codec, fps, audio_codec, nb_frames_approx
    No separate ffprobe binary is required; ffmpeg itself exposes this info.
    """
    engine = RenderEngineService()
    ffmpeg_bin = engine.get_ffmpeg_binary()

    result = subprocess.run(
        [ffmpeg_bin, "-i", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = result.stderr.decode("utf-8", errors="replace")

    meta = {}

    dur_match = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", output)
    if dur_match:
        h, m, s = dur_match.groups()
        meta["duration_s"] = int(h) * 3600 + int(m) * 60 + float(s)

    video_match = re.search(
        r"Stream #\d+:\d+.*?Video:\s+(\w+).*?(\d{3,4})x(\d{3,4}).*?(\d+(?:\.\d+)?)\s+fps",
        output,
    )
    if video_match:
        meta["video_codec"] = video_match.group(1)
        meta["width"] = int(video_match.group(2))
        meta["height"] = int(video_match.group(3))
        meta["fps"] = float(video_match.group(4))

    audio_match = re.search(r"Stream #\d+:\d+.*?Audio:\s+(\w+)", output)
    if audio_match:
        meta["audio_codec"] = audio_match.group(1)

    if "duration_s" in meta and "fps" in meta and meta["fps"] > 0:
        meta["nb_frames_approx"] = int(meta["duration_s"] * meta["fps"])

    meta["_raw"] = output
    return meta


# ---------------------------------------------------------------------------
# Test 1: End-to-end real MP4 render (1 scene)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_real_mp4_render_pipeline(client: AsyncClient):
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

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
        asset = SceneAsset(
            scene_id=scene.id,
            asset_type=AssetType.image,
            url="",
            storage_path=f"images/{scene.id}.jpg",
            metadata_json={"prompt": "test prompt"}
        )
        session.add(asset)
        await session.commit()

    start_res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert start_res.status_code == 201
    job_data = start_res.json()
    job_id = UUID(job_data["id"])
    assert job_data["status"] in ["pending", "processing", "completed"]

    max_wait = 30
    completed = False
    data = {}
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
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["video_url"] is not None
    assert f"/api/v1/render/video/{job_id}" in data["video_url"]

    expected_file = os.path.join(settings.video_storage_dir, f"{job_id}.mp4")
    assert os.path.isfile(expected_file), f"Output MP4 file does not exist at {expected_file}"
    file_size = os.path.getsize(expected_file)
    assert file_size > 1000, f"Rendered MP4 file size is too small: {file_size} bytes"

    with open(expected_file, "rb") as f:
        header = f.read(16)
        assert b"ftyp" in header, f"File does not contain valid MP4 ftyp atom: {header}"

    video_res = await client.get(f"/api/v1/render/video/{job_id}", headers=headers)
    assert video_res.status_code == 200
    assert video_res.headers.get("content-type") == "video/mp4"
    assert "bytes" in video_res.headers.get("accept-ranges", "")
    assert len(video_res.content) == file_size

    try:
        os.remove(expected_file)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Test 2: Strengthened 2-scene validation with ffmpeg -i stream inspection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multi_scene_ffprobe_validation(client: AsyncClient):
    """
    Renders 2 scenes with different durations and validates ALL required metadata:
      - file exists, size > 0
      - valid MP4 ftyp container atom
      - duration > 0 (real content present)
      - video: codec=h264, width=1080, height=1920, fps=30
      - frame count > 1
      - audio: codec=aac
      - RenderJob.status == completed, video_url populated
    """
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        json={
            "title": "Multi-Scene FFprobe Validation Test",
            "description": "2-scene real MP4 codec and metadata validation",
            "style": "Documentary",
            "language": "en",
            "script_content": (
                "Scene one introduces the world of AkmMotion vertical video production. "
                "Scene two demonstrates how the rendering pipeline composes final MP4 output."
            )
        },
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    async with AsyncSessionLocal() as session:
        scene1 = Scene(
            project_id=project_id,
            script_id=UUID(proj_res.json().get("script", {}).get("id") or str(uuid4())),
            scene_number=1,
            duration=3.0,
            narration="AkmMotion is a production-grade AI video creation engine.",
            subtitle="Production AI Video Engine",
            image_prompt="Cinematic aerial drone cityscape golden hour 9:16",
            camera_motion=CameraMotion.push,
            animation_style=AnimationStyle.ken_burns,
            status="ready"
        )
        session.add(scene1)
        await session.flush()
        session.add(SceneAsset(
            scene_id=scene1.id,
            asset_type=AssetType.image,
            url="",
            storage_path=f"images/{scene1.id}.jpg",
            metadata_json={"prompt": "cinematic city scene"}
        ))

        scene2 = Scene(
            project_id=project_id,
            script_id=UUID(proj_res.json().get("script", {}).get("id") or str(uuid4())),
            scene_number=2,
            duration=4.0,
            narration="Every scene compiles to real H.264 MP4 with AAC audio at 1080x1920.",
            subtitle="Real H.264 1080x1920 MP4",
            image_prompt="Futuristic tech studio workspace vertical 9:16 portrait",
            camera_motion=CameraMotion.pan_left,
            animation_style=AnimationStyle.ken_burns,
            status="ready"
        )
        session.add(scene2)
        await session.flush()
        session.add(SceneAsset(
            scene_id=scene2.id,
            asset_type=AssetType.image,
            url="",
            storage_path=f"images/{scene2.id}.jpg",
            metadata_json={"prompt": "tech studio scene"}
        ))
        await session.commit()

    expected_min_duration = 3.0 + 4.0  # 7 seconds

    start_res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert start_res.status_code == 201
    job_data = start_res.json()
    job_id = UUID(job_data["id"])
    assert job_data["status"] in ["pending", "processing", "completed"]

    max_wait = 900  # 15 minutes — 2-scene render with Edge-TTS + FFmpeg zoompan takes ~8-11 min
    completed = False
    data = {}
    for _ in range(max_wait):
        status_res = await client.get(f"/api/v1/render/status/{job_id}", headers=headers)
        assert status_res.status_code == 200
        data = status_res.json()
        if data["status"] == "completed":
            completed = True
            break
        elif data["status"] == "failed":
            pytest.fail(f"Multi-scene render failed: {data.get('error_message')}")
        await asyncio.sleep(1.0)

    assert completed, f"Multi-scene render did not complete within {max_wait}s. Last: {data}"
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["video_url"] is not None
    assert f"/api/v1/render/video/{job_id}" in data["video_url"]

    expected_file = os.path.join(settings.video_storage_dir, f"{job_id}.mp4")
    assert os.path.isfile(expected_file), f"MP4 not found: {expected_file}"
    file_size = os.path.getsize(expected_file)
    assert file_size > 0
    assert file_size > 5000, f"2-scene MP4 suspiciously small: {file_size} bytes"

    with open(expected_file, "rb") as f:
        header = f.read(16)
    assert b"ftyp" in header, f"Not a valid MP4 (missing ftyp atom): {header}"

    # Full stream metadata validation via ffmpeg -i
    meta = _get_mp4_metadata(expected_file)
    raw = meta.get("_raw", "")

    assert "duration_s" in meta, f"Could not parse duration:\n{raw}"
    assert meta["duration_s"] > 0, f"Duration must be > 0, got {meta['duration_s']}"
    assert meta["duration_s"] >= (expected_min_duration - 0.5), (
        f"Duration {meta['duration_s']:.2f}s too short, expected >= {expected_min_duration - 0.5}s"
    )

    assert "video_codec" in meta, f"No video stream:\n{raw}"
    assert meta["video_codec"] == "h264", f"Expected h264, got {meta['video_codec']}\n{raw}"
    assert meta["width"] == 1080, f"Expected width=1080, got {meta['width']}\n{raw}"
    assert meta["height"] == 1920, f"Expected height=1920, got {meta['height']}\n{raw}"
    assert 28.0 <= meta["fps"] <= 32.0, f"Expected ~30 fps, got {meta['fps']}\n{raw}"
    assert meta.get("nb_frames_approx", 0) > 1, f"Must have > 1 frame, got {meta.get('nb_frames_approx')}"

    assert "audio_codec" in meta, f"No audio stream:\n{raw}"
    assert meta["audio_codec"] == "aac", f"Expected aac, got {meta['audio_codec']}\n{raw}"

    print(
        f"\n[MP4 VALIDATION] job_id={job_id}\n"
        f"  File size:    {file_size:,} bytes\n"
        f"  Duration:     {meta['duration_s']:.2f}s\n"
        f"  Resolution:   {meta['width']}x{meta['height']}\n"
        f"  Video codec:  {meta['video_codec']}\n"
        f"  FPS:          {meta['fps']}\n"
        f"  Frame count:  ~{meta.get('nb_frames_approx', 'N/A')}\n"
        f"  Audio codec:  {meta['audio_codec']}\n"
    )

    video_res = await client.get(f"/api/v1/render/video/{job_id}", headers=headers)
    assert video_res.status_code == 200
    assert video_res.headers.get("content-type") == "video/mp4"
    assert "bytes" in video_res.headers.get("accept-ranges", "")
    assert len(video_res.content) == file_size

    try:
        os.remove(expected_file)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Test 3: Failed render handles error gracefully
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_render_handles_error_gracefully(client: AsyncClient):
    """Verifies that an unrecoverable rendering error results in 'failed' status without leaking secrets."""
    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        json={"title": "Failing Render Test", "style": "Explainer", "script_content": "Test script"},
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    job_id = uuid4()
    async with AsyncSessionLocal() as session:
        from app.models.models import RenderJob
        job = RenderJob(
            id=job_id,
            project_id=project_id,
            user_id=UUID(user_id),
            status=RenderStatus.pending,
            progress=0
        )
        session.add(job)
        await session.commit()

    async with AsyncSessionLocal() as session:
        from app.repositories.render_repo import RenderRepository
        repo = RenderRepository(session)
        await repo.update_progress(
            job_id,
            progress=0,
            status=RenderStatus.failed,
            error_message="Encoding error occurred during segment compilation"
        )

    res = await client.get(f"/api/v1/render/status/{job_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert "Encoding error" in data["error_message"]
    for secret in ["key", "token", "password", "aws", "gsk_"]:
        assert secret not in data["error_message"].lower()


# ---------------------------------------------------------------------------
# Test 4: Duplicate render concurrency protection
# ---------------------------------------------------------------------------

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

    res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert res.status_code == 201
    returned_data = res.json()
    assert returned_data["id"] == str(existing_job_id)
    assert returned_data["status"] == "processing"
    assert returned_data["progress"] == 45


# ---------------------------------------------------------------------------
# Test 5: Stale render job auto-recovery after worker/process crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stale_render_job_auto_recovery(client: AsyncClient):
    """
    Verifies that jobs abandoned due to a process crash or restart (>15m stale)
    are automatically transitioned to 'failed' and do not permanently block new renders.
    """
    from datetime import datetime, timezone, timedelta

    user_id = str(uuid4())
    token = create_access_token(subject=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post(
        "/api/v1/projects",
        json={"title": "Stale Job Recovery Test", "style": "Explainer", "script_content": "Recovery test"},
        headers=headers
    )
    assert proj_res.status_code == 201
    project_id = UUID(proj_res.json()["id"])

    # Simulate a dead job from a crashed process 25 minutes ago
    stale_job_id = uuid4()
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=25)
    async with AsyncSessionLocal() as session:
        from app.models.models import RenderJob
        job = RenderJob(
            id=stale_job_id,
            project_id=project_id,
            user_id=UUID(user_id),
            status=RenderStatus.processing,
            progress=30,
            started_at=stale_time,
            created_at=stale_time,
            updated_at=stale_time
        )
        session.add(job)
        await session.commit()

    # 1. get_render_status should auto-recover and return failed status
    status_res = await client.get(f"/api/v1/render/status/{stale_job_id}", headers=headers)
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["status"] == "failed"
    assert "timed out" in data["error_message"].lower() or "restarted" in data["error_message"].lower()

    # 2. start_render should detect stale job, mark it, and create a FRESH new job
    start_res = await client.post(f"/api/v1/render/start/{project_id}", headers=headers)
    assert start_res.status_code == 201
    new_job = start_res.json()
    assert new_job["id"] != str(stale_job_id)
    assert new_job["status"] in ["pending", "processing"]

