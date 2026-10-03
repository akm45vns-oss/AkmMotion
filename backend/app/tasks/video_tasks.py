import asyncio
import logging
from uuid import UUID
from typing import Optional
from fastapi import BackgroundTasks

from app.tasks.celery_app import celery_app
from app.models.models import RenderStatus
from app.db.session import AsyncSessionLocal
from app.repositories.render_repo import RenderRepository
from app.services.render_service import RenderService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, acks_late=True, name="video_tasks.render_video_task")
def render_video_task(self, job_id_str: str, project_id_str: str, user_id_str: str):
    """
    Authoritative Celery worker task for executing heavy FFmpeg rendering.
    Enforces task idempotency, exponential backoff, and heartbeat tracking.
    """
    job_id = UUID(job_id_str)
    project_id = UUID(project_id_str)
    user_id = UUID(user_id_str)

    logger.info(f"[Celery] Starting render task for job {job_id} (attempt {self.request.retries + 1})")

    # Idempotency check via async session
    async def check_and_run():
        async with AsyncSessionLocal() as session:
            repo = RenderRepository(session)
            job = await repo.get_by_id(job_id)
            if not job:
                logger.error(f"[Celery] Job {job_id} not found in database. Aborting.")
                return

            # If already completed or cancelled, skip
            if job.status in [RenderStatus.completed, RenderStatus.cancelled]:
                logger.info(f"[Celery] Job {job_id} already in status {job.status}. Skipping duplicate execution.")
                return

            # Update celery task id and retry count
            job.celery_task_id = str(self.request.id or "")
            job.retry_count = self.request.retries
            await session.commit()

        # Execute actual rendering
        await RenderService.execute_render_background(job_id, project_id, user_id)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_run())
        finally:
            loop.close()

    except Exception as exc:
        logger.exception(f"[Celery] Render task error for job {job_id}: {exc}")
        if self.request.retries < self.max_retries:
            countdown = int(2 ** self.request.retries * 5)
            logger.warning(f"[Celery] Retrying job {job_id} in {countdown}s (retry {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"[Celery] Job {job_id} exhausted all retries. Setting final failed status.")
            async def mark_failed():
                async with AsyncSessionLocal() as session:
                    repo = RenderRepository(session)
                    await repo.update_progress(
                        job_id,
                        progress=0,
                        status=RenderStatus.failed,
                        error_message="Video rendering failed after all retry attempts."
                    )
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(mark_failed())
                loop.close()
            except Exception as final_exc:
                logger.error(f"Failed to update final status for {job_id}: {final_exc}")
            raise exc


def dispatch_render_job(
    job_id: UUID,
    project_id: UUID,
    user_id: UUID,
    background_tasks: Optional[BackgroundTasks] = None
) -> str:
    """
    Dispatches a render job to Celery queue if broker is reachable.
    Gracefully falls back to async background execution if Celery broker is offline or in local dev.
    Returns the dispatch mechanism ('celery' or 'background_task').
    """
    from app.core.config import settings
    
    if not settings.CELERY_TASK_ALWAYS_EAGER:
        try:
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(settings.CELERY_BROKER_URL)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 6379
            with socket.create_connection((host, port), timeout=0.1):
                pass

            task = render_video_task.apply_async(
                args=[str(job_id), str(project_id), str(user_id)]
            )
            logger.info(f"Dispatched render job {job_id} to Celery queue (task ID: {task.id})")
            return "celery"
        except Exception as exc:
            logger.warning(f"Celery broker unavailable ({exc}); falling back to in-process background task.")

    if background_tasks is not None:
        background_tasks.add_task(RenderService.execute_render_background, job_id, project_id, user_id)
    else:
        asyncio.create_task(RenderService.execute_render_background(job_id, project_id, user_id))
    return "background_task"
