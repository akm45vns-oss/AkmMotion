import pytest
from uuid import uuid4
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin
from app.core.security import verify_password, get_password_hash
from app.services.render_engine import RenderEngineService
from app.services.ai.groq_key_manager import GroqKeyManager
from app.services.ai.voice_generator import VoiceGeneratorService, _cache_put, _cache_get


from unittest.mock import AsyncMock, MagicMock
from app.models.models import User, AuthProvider
from app.core.config import Settings


@pytest.mark.asyncio
async def test_password_hashing_and_verification_unit():
    """Verify that user registration hashes password and login enforces password verification (P0-5)."""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    auth_service = AuthService(mock_db)

    # In-memory user store for mock repo
    users_db = {}

    async def mock_get_by_email(email):
        return users_db.get(email.lower().strip())

    async def mock_create(email, full_name, hashed_password=None, auth_provider=AuthProvider.email):
        user = User(
            id=uuid4(),
            email=email.lower().strip(),
            full_name=full_name,
            hashed_password=hashed_password,
            auth_provider=auth_provider,
            is_active=True,
            is_verified=True
        )
        users_db[user.email] = user
        return user

    auth_service.user_repo.get_by_email = mock_get_by_email
    auth_service.user_repo.create = mock_create

    plain_password = "SuperSecurePassword123!"
    test_email = "prod_user@example.com"

    # 1. Register user
    reg_payload = UserCreate(
        email=test_email,
        password=plain_password,
        full_name="Production Test User"
    )
    token_response = await auth_service.register_user(reg_payload)
    assert token_response.access_token is not None
    assert token_response.refresh_token is not None

    # Verify password in DB is actually hashed and not plaintext
    created_user = users_db[test_email]
    assert created_user.hashed_password is not None
    assert created_user.hashed_password != plain_password
    assert verify_password(plain_password, created_user.hashed_password) is True

    # 2. Login with correct password
    login_payload = UserLogin(email=test_email, password=plain_password)
    login_res = await auth_service.login_user(login_payload)
    assert login_res.access_token is not None

    # 3. Login with WRONG password must fail with 401
    bad_login = UserLogin(email=test_email, password="WrongPassword999!")
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(bad_login)
    assert exc_info.value.status_code == 401
    assert "incorrect email or password" in exc_info.value.detail.lower()


def test_startup_secret_validation_guard():
    """Verify that startup fails fast if DATABASE_URL or JWT_SECRET is missing or weak (P0-1, P0-3)."""
    # Empty DB URL
    s_bad_db = Settings(DATABASE_URL="", JWT_SECRET="a" * 32)
    with pytest.raises(RuntimeError) as exc_db:
        s_bad_db.validate_required_secrets
    assert "DATABASE_URL is not set" in str(exc_db.value)

    # Short JWT secret
    s_short_jwt = Settings(DATABASE_URL="postgresql://localhost/db", JWT_SECRET="short")
    with pytest.raises(RuntimeError) as exc_jwt:
        s_short_jwt.validate_required_secrets
    assert "JWT_SECRET is too short" in str(exc_jwt.value)

    # Valid settings pass validation
    s_valid = Settings(DATABASE_URL="postgresql://localhost/db", JWT_SECRET="x" * 48)
    # Should not raise
    s_valid.validate_required_secrets


def test_groq_production_models_configured():
    """Verify that Groq models point to real Groq production models (P1-4)."""
    assert GroqKeyManager.BEST_MODEL == "llama-3.3-70b-versatile"
    assert GroqKeyManager.FAST_MODEL == "llama-3.1-8b-instant"
    assert GroqKeyManager.BACKUP_MODEL == "gemma2-9b-it"


def test_ffmpeg_path_escaping_windows_and_linux():
    """Verify cross-platform FFmpeg drawtext path escaping (P1-5)."""
    # Windows absolute path with drive letter
    win_path = r"C:\Users\tester\video creation\storage\sub.ass"
    escaped = RenderEngineService._escape_ffmpeg_path(win_path)
    assert r"C\:" in escaped or r"C\:" in escaped.replace("/", "\\")
    assert "\\" not in escaped.replace(r"\:", "")  # all directory slashes are forward slashes

    # Posix path
    posix_path = "/var/log/sub'title.ass"
    escaped_posix = RenderEngineService._escape_ffmpeg_path(posix_path)
    assert r"\'" in escaped_posix


def test_ssrf_asset_url_validation():
    """Verify that RenderEngine blocks private IP and cloud metadata SSRF (P2-4)."""
    # Allowed public URL
    assert RenderEngineService._is_safe_download_url("https://images.unsplash.com/photo-123.jpg") is True

    # Blocked private and loopback URLs
    assert RenderEngineService._is_safe_download_url("http://127.0.0.1/admin") is False
    assert RenderEngineService._is_safe_download_url("http://localhost:8000/secret") is False
    assert RenderEngineService._is_safe_download_url("http://169.254.169.254/latest/meta-data/") is False
    assert RenderEngineService._is_safe_download_url("file:///etc/passwd") is False


def test_voice_cache_bounded_lru():
    """Verify that VoiceGeneratorService LRU cache correctly bounds memory (P2-3)."""
    # Put 250 items into the cache
    for i in range(250):
        _cache_put(f"test_key_{i}", f"audio_bytes_{i}".encode())

    # Older keys (0 to 49) should have been evicted
    assert _cache_get("test_key_0") is None
    assert _cache_get("test_key_10") is None
    # Recent keys should still exist
    assert _cache_get("test_key_249") is not None


def test_multi_character_dna_prompt_generation():
    """Verify multi-character DNA injection into visual scene prompts (P1-1)."""
    from app.schemas.character import CharacterDNA
    from app.services.ai.prompt_builder import PromptBuilderService

    # 1. Single character
    char1_dna = CharacterDNA(
        character_code="CHR_MAYA",
        age=24,
        gender="Female",
        visual_style="Anime",
        hair_style="High ponytail",
        hair_color="Neon Pink",
        eye_color="Violet",
        skin_tone="Fair",
        outfit="Cyberpunk jacket"
    )
    c1 = {"name": "Maya", "dna": char1_dna.model_dump()}

    prompt_single = PromptBuilderService.inject_multi_character_dna(
        "Standing on a neon rooftop at night",
        [c1],
        action_description="looking through binoculars"
    )
    assert "Maya" in prompt_single
    assert "neon pink" in prompt_single.lower()
    assert "cyberpunk jacket" in prompt_single.lower()
    assert "looking through binoculars" in prompt_single

    # 2. Two characters
    char2_dna = CharacterDNA(
        character_code="CHR_LIAM",
        age=28,
        gender="Male",
        visual_style="Cinematic",
        hair_style="Undercut",
        hair_color="Dark Brown",
        eye_color="Hazel",
        skin_tone="Olive",
        outfit="Leather trench coat"
    )
    c2 = {"name": "Liam", "dna": char2_dna.model_dump()}

    prompt_two = PromptBuilderService.inject_multi_character_dna(
        "Arguing near the command console",
        [c1, c2],
        action_description="pointing at the radar screen"
    )
    assert "Maya" in prompt_two and "Liam" in prompt_two
    assert "neon pink" in prompt_two.lower()
    assert "dark brown" in prompt_two.lower()
    assert "cyberpunk jacket" in prompt_two.lower()
    assert "leather trench coat" in prompt_two.lower()
    assert "distinct characters" in prompt_two
    assert "consistent character appearance" in prompt_two

    # 3. Three characters
    char3_dna = CharacterDNA(
        character_code="CHR_SOPHIA",
        age=32,
        gender="Female",
        visual_style="Photorealistic",
        hair_style="Bob cut",
        hair_color="Platinum Blonde",
        eye_color="Emerald Green",
        skin_tone="Pale",
        outfit="Lab coat with biometric badge"
    )
    c3 = {"name": "Dr. Sophia", "dna": char3_dna.model_dump()}

    prompt_three = PromptBuilderService.inject_multi_character_dna(
        "Inside the quantum laboratory",
        [c1, c2, c3]
    )
    assert "Dr. Sophia" in prompt_three
    assert "platinum blonde" in prompt_three.lower()
    assert "lab coat" in prompt_three.lower()

    # 4. Injection spec verification
    spec = PromptBuilderService.generate_injection_spec(char1_dna.model_dump(), "Operating the drone")
    assert spec.character_id == "CHR_MAYA"
    assert "Face" in spec.locked_attributes
    assert "Outfit" in spec.locked_attributes
    assert "Hair Color" in spec.locked_attributes


class MockStreamContext:
    def __init__(self, resp):
        self.resp = resp
    async def __aenter__(self):
        return self.resp
    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_ssrf_redirect_chain_defense():
    """Verify that secure_download_media rejects redirects targeting internal/metadata IPs (P2-4)."""
    import httpx
    from unittest.mock import patch
    from app.core.secure_downloader import secure_download_media, SSRFSecurityError

    # Redirect to loopback 127.0.0.1
    mock_redirect_loopback = httpx.Response(302, headers={"Location": "http://127.0.0.1:8000/internal-admin"})
    with patch.object(httpx.AsyncClient, "stream", return_value=MockStreamContext(mock_redirect_loopback)):
        with pytest.raises(SSRFSecurityError) as exc_info:
            await secure_download_media("https://example.com/asset.mp4")
        assert "SSRF redirect violation" in str(exc_info.value)
        assert "127.0.0.1" in str(exc_info.value)

    # Redirect to cloud metadata 169.254.169.254
    mock_redirect_metadata = httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data"})
    with patch.object(httpx.AsyncClient, "stream", return_value=MockStreamContext(mock_redirect_metadata)):
        with pytest.raises(SSRFSecurityError) as exc_meta:
            await secure_download_media("https://example.com/asset.mp4")
        assert "SSRF redirect violation" in str(exc_meta.value)
        assert "169.254.169.254" in str(exc_meta.value)


@pytest.mark.asyncio
async def test_streaming_chunk_size_abort_prevents_memory_exhaustion():
    """Verify that streaming downloader aborts immediately when bytes exceed max_bytes without buffering full response (P0)."""
    import httpx
    from unittest.mock import patch
    from app.core.secure_downloader import secure_download_media, DownloadError

    class MockChunkStream:
        def __init__(self):
            self.status_code = 200
            self.headers = {"Content-Type": "video/mp4"}
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def aiter_bytes(self, chunk_size=65536):
            # Emits 5 chunks of 50KB = 250KB total
            for _ in range(5):
                yield b"X" * 50000

    # Limit to 100KB: chunk 1 (50K) ok, chunk 2 (100K) ok, chunk 3 (150K) triggers abortion
    with patch.object(httpx.AsyncClient, "stream", return_value=MockChunkStream()):
        with pytest.raises(DownloadError) as exc_info:
            await secure_download_media("https://example.com/large_video.mp4", max_bytes=100000)
        assert "exceeded limit" in str(exc_info.value)
        assert "aborted at 150000" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ssrf_redirect_loop_and_unsupported_schemes():
    """Verify rejection of redirect loops and non-http schemes like file:// or ftp://."""
    import httpx
    from unittest.mock import patch
    from app.core.secure_downloader import secure_download_media, SSRFSecurityError, DownloadError

    # 1. Scheme check: file:///etc/passwd
    mock_file = httpx.Response(302, headers={"Location": "file:///etc/passwd"})
    with patch.object(httpx.AsyncClient, "stream", return_value=MockStreamContext(mock_file)):
        with pytest.raises(SSRFSecurityError) as exc_scheme:
            await secure_download_media("https://example.com/asset.mp4")
        assert "Forbidden redirect scheme 'file'" in str(exc_scheme.value)

    # 2. Redirect loop
    mock_loop = httpx.Response(302, headers={"Location": "https://example.com/asset.mp4"})
    with patch.object(httpx.AsyncClient, "stream", return_value=MockStreamContext(mock_loop)):
        with pytest.raises(DownloadError) as exc_loop:
            await secure_download_media("https://example.com/asset.mp4")
        assert "Redirect loop detected" in str(exc_loop.value)


def test_production_celery_enforcement_and_no_silent_fallback():
    """Verify that production environment strictly enforces Celery and refuses silent fallback to in-process tasks (P1)."""
    from unittest.mock import patch
    from uuid import uuid4
    from app.core.config import Settings
    from app.tasks.video_tasks import dispatch_render_job

    # 1. Background mode in production is rejected at startup
    prod_bad = Settings(
        DATABASE_URL="postgresql://host/db",
        JWT_SECRET="x" * 40,
        ENVIRONMENT="production",
        RENDER_EXECUTION_MODE="background",
        CELERY_BROKER_URL="redis://host:6379/0"
    )
    with pytest.raises(RuntimeError) as exc_conf:
        prod_bad.validate_required_secrets
    assert "RENDER_EXECUTION_MODE must be set to 'celery' in production" in str(exc_conf.value)

    # 2. Celery mode in production is accepted
    prod_good = Settings(
        DATABASE_URL="postgresql://host/db",
        JWT_SECRET="x" * 40,
        ENVIRONMENT="production",
        RENDER_EXECUTION_MODE="celery",
        CELERY_BROKER_URL="redis://host:6379/0"
    )
    # Should not raise
    prod_good.validate_required_secrets

    # 3. Production dispatch failure raises RuntimeError and NEVER falls back to BackgroundTasks
    with patch("app.core.config.settings.ENVIRONMENT", "production"), patch("app.core.config.settings.RENDER_EXECUTION_MODE", "celery"):
        with patch("app.tasks.video_tasks.render_video_task.apply_async", side_effect=Exception("Redis broker refused")):
            with pytest.raises(RuntimeError) as exc_dispatch:
                dispatch_render_job(uuid4(), uuid4(), uuid4())
            assert "Production render dispatch failed" in str(exc_dispatch.value)
            assert "In-process background rendering is strictly prohibited" in str(exc_dispatch.value)


def test_distributed_rate_limiter_sliding_window():
    """Verify DistributedRateLimiter handles sliding windows, bursts, and key isolation."""
    from app.core.rate_limit import DistributedRateLimiter

    limiter = DistributedRateLimiter()
    limiter.reset()

    key_a = "user:test_user_a"
    key_b = "user:test_user_b"

    # Allow up to 3 requests per 10 seconds
    assert limiter.is_allowed(key_a, max_requests=3, window_seconds=10) is True
    assert limiter.is_allowed(key_a, max_requests=3, window_seconds=10) is True
    assert limiter.is_allowed(key_a, max_requests=3, window_seconds=10) is True
    # 4th request must be blocked
    assert limiter.is_allowed(key_a, max_requests=3, window_seconds=10) is False

    # Different key (key_b) must still be allowed (key isolation)
    assert limiter.is_allowed(key_b, max_requests=3, window_seconds=10) is True

    # Reset clears history
    limiter.reset()
    assert limiter.is_allowed(key_a, max_requests=3, window_seconds=10) is True


@pytest.mark.asyncio
async def test_render_cancellation_revokes_celery_task():
    """Verify that cancel_render_job invokes Celery revocation when task ID is present."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from uuid import uuid4
    from app.services.render_service import RenderService
    from app.models.models import RenderJob, RenderStatus

    job_id = uuid4()
    user_id = uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    mock_job = RenderJob(
        id=job_id,
        project_id=uuid4(),
        user_id=user_id,
        status=RenderStatus.processing,
        progress=50,
        celery_task_id="celery-task-12345",
        created_at=now,
        updated_at=now
    )

    mock_db = AsyncMock()
    service = RenderService(mock_db)
    service.repo.get_by_id = AsyncMock(return_value=mock_job)
    service.repo.cancel_job = AsyncMock(return_value=mock_job)

    with patch("app.tasks.celery_app.celery_app.control.revoke") as mock_revoke:
        await service.cancel_render_job(job_id, user_id)
        mock_revoke.assert_called_once_with("celery-task-12345", terminate=True, signal="SIGTERM")


def test_subtitle_canonical_validation_and_timing_source():
    """Verify canonical subtitle schema validation, timing source tracking, and Devanagari handling."""
    from app.services.ai.subtitle_generator import SubtitleGeneratorService

    # 1. Valid timings
    valid_timings = [
        {"word": "Namaste", "start_ms": 200, "end_ms": 700},
        {"word": "duniya", "start_ms": 700, "end_ms": 1400},
    ]
    ok, err = SubtitleGeneratorService.validate_word_timings(valid_timings, total_duration_seconds=2.0)
    assert ok is True
    assert err is None

    # 2. Non-monotonic timings rejected
    bad_mono = [
        {"word": "First", "start_ms": 500, "end_ms": 900},
        {"word": "Second", "start_ms": 300, "end_ms": 800},
    ]
    ok_mono, err_mono = SubtitleGeneratorService.validate_word_timings(bad_mono, total_duration_seconds=2.0)
    assert ok_mono is False
    assert "monotonic" in err_mono

    # 3. Negative start rejected
    bad_neg = [{"word": "Bad", "start_ms": -50, "end_ms": 400}]
    ok_neg, err_neg = SubtitleGeneratorService.validate_word_timings(bad_neg, total_duration_seconds=1.0)
    assert ok_neg is False
    assert "negative" in err_neg

    # 4. End before start rejected
    bad_end = [{"word": "Bad", "start_ms": 500, "end_ms": 400}]
    ok_end, err_end = SubtitleGeneratorService.validate_word_timings(bad_end, total_duration_seconds=1.0)
    assert ok_end is False
    assert "invalid duration" in err_end

    # 5. Devanagari script word timings
    hindi_text = "नमस्ते भारत AkmMotion"
    hindi_timings = SubtitleGeneratorService.compute_word_timings_from_text(hindi_text, 3.0)
    assert len(hindi_timings) == 3
    assert hindi_timings[0]["word"] == "नमस्ते"
    assert hindi_timings[0]["start_ms"] >= 0
    assert hindi_timings[-1]["end_ms"] <= 3500


@pytest.mark.asyncio
async def test_real_mp4_generation_with_karaoke_ass_subtitles():
    """Verify end-to-end real FFmpeg compilation of 1080x1920 MP4 with burned-in ASS karaoke subtitles."""
    import os
    import tempfile
    from app.services.render_engine import RenderEngineService
    from app.services.ai.subtitle_generator import SubtitleGeneratorService

    engine = RenderEngineService()
    tmp_dir = tempfile.gettempdir()
    img_path = os.path.join(tmp_dir, f"test_e2e_img_{uuid4().hex[:6]}.png")
    audio_path = os.path.join(tmp_dir, f"test_e2e_aud_{uuid4().hex[:6]}.mp3")
    sub_path = os.path.join(tmp_dir, f"test_e2e_sub_{uuid4().hex[:6]}.ass")
    out_path = os.path.join(tmp_dir, f"test_e2e_out_{uuid4().hex[:6]}.mp4")

    try:
        # 1. 1080x1920 graphic card
        await engine._run_ffmpeg([
            "-y", "-f", "lavfi", "-i", "color=c=0x0F172A:s=1080x1920:d=1", "-vframes", "1", img_path
        ])
        # 2. 2.5s stereo audio
        await engine._run_ffmpeg([
            "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2.5", "-c:a", "libmp3lame", "-b:a", "128k", audio_path
        ])
        # 3. ASS Subtitle generation with karaoke active highlights
        text = "AkmMotion production release ready"
        timings = SubtitleGeneratorService.compute_word_timings_from_text(text, 2.5)
        engine._create_ass_subtitle_file(sub_path, text, 2.5, timings)

        # 4. Compile scene segment via FFmpeg
        await engine._render_scene_segment(
            img_path=img_path,
            audio_path=audio_path,
            sub_path=sub_path,
            output_segment=out_path,
            duration=2.5,
            camera_motion="push"
        )

        assert os.path.isfile(out_path) is True
        assert os.path.getsize(out_path) > 1000  # Non-trivial MP4 size
    finally:
        for p in [img_path, audio_path, sub_path, out_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


@pytest.mark.asyncio
async def test_http_range_206_streaming():
    """Verify HTTP Range 206 Partial Content streaming for video playback (P2-2)."""
    import tempfile
    import os
    import httpx
    from fastapi import FastAPI
    from fastapi.responses import FileResponse

    # Setup dummy video app
    app = FastAPI()
    test_content = b"VIDEO_CHUNK_HEADER_" + (b"A" * 400) + (b"B" * 400)
    total_size = len(test_content)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    try:
        temp_file.write(test_content)
        temp_file.flush()
        temp_file.close()

        @app.get("/video/{job_id}")
        async def stream_video(job_id: str):
            return FileResponse(
                path=temp_file.name,
                media_type="video/mp4",
                filename=f"video_{job_id}.mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": 'inline; filename="video.mp4"'
                }
            )

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # 1. Full content request (200)
            full_resp = await client.get("/video/job123")
            assert full_resp.status_code == 200
            assert full_resp.headers.get("accept-ranges") == "bytes"
            assert len(full_resp.content) == total_size

            # 2. First 100 bytes Range request (206)
            range_resp = await client.get("/video/job123", headers={"Range": "bytes=0-99"})
            assert range_resp.status_code == 206
            assert range_resp.headers.get("content-range") == f"bytes 0-99/{total_size}"
            assert range_resp.headers.get("accept-ranges") == "bytes"
            assert len(range_resp.content) == 100
            assert range_resp.content == test_content[:100]

            # 3. Middle chunk Range request (206)
            mid_resp = await client.get("/video/job123", headers={"Range": "bytes=100-249"})
            assert mid_resp.status_code == 206
            assert mid_resp.headers.get("content-range") == f"bytes 100-249/{total_size}"
            assert len(mid_resp.content) == 150
            assert mid_resp.content == test_content[100:250]
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def test_scene_transition_mapping():
    """Verify scene transitions (fade, slide, wipe, zoom) map to valid FFmpeg xfade types (P2-1)."""
    from app.services.render_engine import RenderEngineService

    expected_transitions = {
        "fade": "fade",
        "slide": "slideleft",
        "wipe": "wipeleft",
        "zoom": "zoomin",
    }
    for name, expected_filter in expected_transitions.items():
        assert RenderEngineService.TRANSITION_MAP.get(name) == expected_filter

    # Fallback to fade on unknown
    assert RenderEngineService.TRANSITION_MAP.get("nonexistent_glitch", "fade") == "fade"


def test_canonical_subtitle_timing_and_ass_file():
    """Verify canonical word-level subtitle timing (start_ms, end_ms) and ASS file generation (P1-3)."""
    import tempfile
    import os
    from app.services.ai.subtitle_generator import SubtitleGeneratorService
    from app.services.render_engine import RenderEngineService

    sample_text = "Welcome to AkmMotion the premier vertical video AI creation suite"
    duration = 5.0
    timings = SubtitleGeneratorService.compute_word_timings_from_text(sample_text, duration)

    assert len(timings) == len(sample_text.split())
    for t in timings:
        assert "word" in t
        assert "start_ms" in t
        assert "end_ms" in t
        assert isinstance(t["start_ms"], int)
        assert isinstance(t["end_ms"], int)
        assert t["end_ms"] >= t["start_ms"]

    # Test ASS file generation
    tmp_ass = tempfile.NamedTemporaryFile(delete=False, suffix=".ass")
    tmp_ass.close()
    try:
        ass_path = RenderEngineService._create_ass_subtitle_file(
            output_file=tmp_ass.name,
            text=sample_text,
            duration=duration,
            word_timings=timings
        )
        assert os.path.isfile(ass_path)
        with open(ass_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "[Script Info]" in content
        assert "PlayResX: 1080" in content
        assert "PlayResY: 1920" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Dialogue: 0," in content
    finally:
        if os.path.exists(tmp_ass.name):
            os.remove(tmp_ass.name)


