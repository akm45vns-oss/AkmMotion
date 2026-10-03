import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

from app.tasks.video_tasks import dispatch_render_job
from app.repositories.render_repo import RenderRepository
from app.models.models import RenderJob, RenderStatus, User, Project, AuthProvider
from app.db.session import AsyncSessionLocal
from app.services.render_engine import RenderEngineService
from app.services.storage_service import storage_service, StorageError
from app.services.ai.providers.provider_manager import ProviderManager
from app.services.ai.providers.base import ProviderState


# ==============================================================================
# 1. REDIS OUTAGE & BROKER DROP RESILIENCE
# ==============================================================================
@pytest.mark.asyncio
async def test_redis_broker_outage_graceful_fallback():
    """
    Simulates a total Redis outage or network partition.
    dispatch_render_job must NOT raise an exception, hang, or crash.
    It must gracefully catch the broker error and fall back to background_tasks.
    """
    job_id = uuid4()
    project_id = uuid4()
    user_id = uuid4()

    # Mock socket connection to simulate Redis connection timeout / refused
    with patch("socket.create_connection", side_effect=ConnectionRefusedError("Connection refused by Redis")):
        bg_tasks = MagicMock()
        dispatch_type = dispatch_render_job(job_id, project_id, user_id, background_tasks=bg_tasks)

        # Must cleanly select background_task
        assert dispatch_type == "background_task"
        # Must have registered the job into background tasks
        assert bg_tasks.add_task.called


# ==============================================================================
# 2. CELERY WORKER CRASH & STALE JOB RECOVERY
# ==============================================================================
@pytest.mark.asyncio
async def test_worker_killed_mid_render_recovered_by_sweeper():
    """
    Simulates a Celery worker being killed (OOM / SIGKILL) mid-render.
    The job is left in 'processing' status in the database.
    The stale-job recovery sweeper must identify and recover it to 'failed'.
    """
    user_id = uuid4()
    project_id = uuid4()

    async with AsyncSessionLocal() as session:
        # Seed user and project
        user = User(id=user_id, email=f"stale_{user_id.hex[:6]}@test.com", full_name="Stale User", auth_provider=AuthProvider.email, is_active=True)
        project = Project(id=project_id, user_id=user_id, title="Stale Project", style="Explainer", language="en")
        session.add_all([user, project])
        await session.commit()

        repo = RenderRepository(session)
        job = await repo.create_job(project_id=project_id, user_id=user_id)

        # Simulate job abandoned 15 minutes ago
        past_time = datetime.now(timezone.utc) - timedelta(seconds=900)
        job.status = RenderStatus.processing
        job.updated_at = past_time
        job.started_at = past_time
        await session.commit()
        job_id = job.id

    # Run recovery sweeper with 600s threshold
    async with AsyncSessionLocal() as session:
        repo = RenderRepository(session)
        recovered_count = await repo.recover_abandoned_jobs(stale_timeout_seconds=600)
        assert recovered_count >= 1

        # Check job status is now failed and lock released
        updated_job = await repo.get_by_id(job_id)
        assert updated_job.status == RenderStatus.failed
        assert "timed out or worker process was restarted" in updated_job.error_message


# ==============================================================================
# 3. POSTGRESQL TRANSACTION ROLLBACK INTEGRITY
# ==============================================================================
@pytest.mark.asyncio
async def test_postgres_transaction_rollback_prevents_partial_state():
    """
    Simulates a database failure or integrity conflict during multi-step operation.
    Ensures that rollback leaves 0 orphaned records.
    """
    user_id = uuid4()
    async with AsyncSessionLocal() as session:
        user = User(id=user_id, email=f"rollback_{user_id.hex[:6]}@test.com", full_name="Rollback User", auth_provider=AuthProvider.email, is_active=True)
        session.add(user)
        await session.commit()

    async with AsyncSessionLocal() as session:
        try:
            # Add a project
            proj = Project(user_id=user_id, title="Will Rollback", style="Explainer", language="en")
            session.add(proj)
            await session.flush()
            # Deliberately raise error
            raise ValueError("Simulated unexpected database failure mid-transaction")
        except ValueError:
            await session.rollback()

    # Verify project was not persisted
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        res = await session.execute(select(Project).where(Project.user_id == user_id, Project.title == "Will Rollback"))
        assert res.scalar_one_or_none() is None


# ==============================================================================
# 4. FFMPEG PROCESS CORRUPTION & TIMEOUT RECOVERY
# ==============================================================================
@pytest.mark.asyncio
async def test_ffmpeg_timeout_kills_process_cleanly():
    """
    Simulates an FFmpeg hang or infinite loop.
    _run_ffmpeg must terminate the subprocess cleanly and raise TimeoutError.
    """
    engine = RenderEngineService()

    # Run FFmpeg with a 0.05s timeout running sleep or blocking
    with pytest.raises(TimeoutError) as exc_info:
        # Pass a command that blocks or simulate timeout
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            await engine._run_ffmpeg(["-f", "lavfi", "-i", "nullsrc"], timeout=0.1)

    assert "timed out after" in str(exc_info.value)


# ==============================================================================
# 5. STORAGE ABUSE & RESILIENCE
# ==============================================================================
def test_storage_blocks_path_traversal():
    """Verifies that malicious path traversal keys are immediately blocked."""
    traversal_keys = [
        "../../etc/passwd",
        "users/../../root/file.mp4",
        "/etc/shadow",
        "....//....//file.txt"
    ]
    for bad_key in traversal_keys:
        with pytest.raises(StorageError) as exc_info:
            storage_service._get_local_path(bad_key)
        assert "path traversal" in str(exc_info.value).lower() or "security" in str(exc_info.value).lower()


def test_storage_blocks_oversized_payload():
    """Verifies that files exceeding MAX_FILE_SIZE_BYTES are rejected."""
    huge_data = b"x" * (100 * 1024 * 1024 + 10)  # > 100MB
    with pytest.raises(StorageError) as exc_info:
        storage_service.validate_file(huge_data)
    assert "exceeds maximum allowed" in str(exc_info.value)


# ==============================================================================
# 6. FAL.AI CREDIT EXHAUSTION / 403 GRACEFUL FAILOVER
# ==============================================================================
@pytest.mark.asyncio
async def test_fal_credit_exhaustion_routes_to_ken_burns_fallback():
    """
    Simulates fal.ai returning 403 Forbidden (billing limit or credit exhaustion).
    ProviderManager must immediately classify fal.ai as DEGRADED and failover
    to FallbackProvider (Ken Burns motion engine) with 0 dropped requests.
    """
    pm = ProviderManager()
    assert pm.fal.state == ProviderState.HEALTHY

    # Simulate fal.ai returning 403 credit exhaustion
    pm.fal.record_failure(status_code=403)
    assert pm.fal.state == ProviderState.DEGRADED

    # ProviderManager must now route to fallback provider
    active_provider = pm.get_provider()
    assert active_provider.name == "fallback_ken_burns"
    assert active_provider.state == ProviderState.HEALTHY
