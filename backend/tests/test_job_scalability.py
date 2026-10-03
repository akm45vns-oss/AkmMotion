import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.db.session import AsyncSessionLocal
from app.models.models import RenderJob, RenderStatus, Project, User, AuthProvider
from app.repositories.render_repo import RenderRepository
from app.services.render_service import RenderService
from app.core.config import settings
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_job_capacity_controls_per_user():
    async with AsyncSessionLocal() as db:
        repo = RenderRepository(db)
        # Clear any stale jobs from other test runs so global capacity isn't full
        await repo.recover_abandoned_jobs(stale_timeout_seconds=0)

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"scalability_{user_id}@test.com",
            full_name="Scale Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)

        # Create two projects
        p1 = Project(id=uuid4(), user_id=user_id, title="P1", style="Cinematic")
        p2 = Project(id=uuid4(), user_id=user_id, title="P2", style="Cinematic")
        db.add_all([p1, p2])
        await db.commit()

        render_service = RenderService(db)

        # Mock dispatch so background worker doesn't immediately fail the empty project
        with patch("app.tasks.video_tasks.dispatch_render_job", return_value="mocked"):
            with patch.object(render_service.repo, "count_active_jobs_global", return_value=0):
                # 1. Start render on P1
                job1 = await render_service.start_render_job(p1.id, str(user_id))
                assert job1 is not None

                # 2. Attempt starting render on P2 should hit MAX_CONCURRENT_RENDERS_PER_USER
                with pytest.raises(HTTPException) as exc:
                    await render_service.start_render_job(p2.id, str(user_id))
                assert exc.value.status_code == 429
                assert "active render job in progress" in str(exc.value.detail)

                # Cleanup
                await repo.cancel_job(job1.id, user_id)


@pytest.mark.asyncio
async def test_job_cancellation():
    async with AsyncSessionLocal() as db:
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"cancel_{user_id}@test.com",
            full_name="Cancel Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        project = Project(id=uuid4(), user_id=user_id, title="Cancel P", style="Cinematic")
        db.add(project)
        await db.commit()

        repo = RenderRepository(db)
        job = await repo.create_job(project_id=project.id, user_id=user_id)

        # Cancel job
        cancelled_job = await repo.cancel_job(job.id, user_id)
        assert cancelled_job is not None
        assert cancelled_job.status == RenderStatus.cancelled
        assert "cancelled" in (cancelled_job.error_message or "").lower()

        # Idempotent cancel
        cancelled_again = await repo.cancel_job(job.id, user_id)
        assert cancelled_again.status == RenderStatus.cancelled


@pytest.mark.asyncio
async def test_recover_abandoned_jobs():
    user_id = uuid4()
    job_id = None

    async with AsyncSessionLocal() as db:
        user = User(
            id=user_id,
            email=f"abandon_{user_id}@test.com",
            full_name="Abandon Tester",
            auth_provider=AuthProvider.email
        )
        db.add(user)
        project = Project(id=uuid4(), user_id=user_id, title="Abandon P", style="Cinematic")
        db.add(project)
        await db.commit()

        repo = RenderRepository(db)
        stale_job = await repo.create_job(project_id=project.id, user_id=user_id)
        job_id = stale_job.id
        await repo.update_progress(stale_job.id, progress=50, status=RenderStatus.processing)

        # Force timestamps into the past (20 minutes ago)
        from sqlalchemy import text
        twenty_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=20)
        await db.execute(
            text("UPDATE render_jobs SET updated_at = :stale_time, started_at = :stale_time, created_at = :stale_time WHERE id = :job_id"),
            {"stale_time": twenty_mins_ago, "job_id": stale_job.id}
        )
        await db.commit()
        db.expire_all()

        # Recover jobs abandoned longer than 10 minutes (600s)
        recovered_count = await repo.recover_abandoned_jobs(stale_timeout_seconds=600)
        assert recovered_count >= 1

    # Read with fresh session to avoid stale identity map
    async with AsyncSessionLocal() as db_read:
        repo_read = RenderRepository(db_read)
        reloaded = await repo_read.get_by_id(job_id)
        assert reloaded.status == RenderStatus.failed
        assert "timed out" in (reloaded.error_message or "").lower()
