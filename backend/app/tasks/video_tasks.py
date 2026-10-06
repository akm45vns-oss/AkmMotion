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
) -> tuple[str, Optional[str]]:
    """
    Dispatches a render job to the Celery queue.
    In production mode (ENVIRONMENT='production' or RENDER_EXECUTION_MODE='celery'):
      Celery is MANDATORY. If Celery broker is unreachable or task dispatch fails,
      raises RuntimeError immediately. Silent fallback to in-process BackgroundTasks is prohibited.
    In development mode:
      Tries Celery first if broker is reachable; gracefully falls back to BackgroundTasks.
    Returns (dispatch_mode, celery_task_id).
    """
    from app.core.config import settings

    is_production = settings.ENVIRONMENT.lower() == "production"
    is_celery_forced = settings.RENDER_EXECUTION_MODE.lower() == "celery"

    # Production path: Celery is mandatory
    if is_production or is_celery_forced:
        try:
            task = render_video_task.apply_async(
                args=[str(job_id), str(project_id), str(user_id)]
            )
            logger.info(f"[Production] Dispatched render job {job_id} to Celery queue (task ID: {task.id})")
            return "celery", str(task.id)
        except Exception as exc:
            logger.critical(f"[Production] Celery render dispatch failed for job {job_id}: {exc}")
            raise RuntimeError(
                f"Production render dispatch failed: Celery broker is unreachable or failed to enqueue ({exc}). "
                "In-process background rendering is strictly prohibited in production."
            )

    # Development path: attempt Celery if configured, fallback to in-process BackgroundTasks
    if not settings.CELERY_TASK_ALWAYS_EAGER and settings.CELERY_BROKER_URL:
        try:
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(settings.CELERY_BROKER_URL)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 6379
            with socket.create_connection((host, port), timeout=0.15):
                pass

            task = render_video_task.apply_async(
                args=[str(job_id), str(project_id), str(user_id)]
            )
            logger.info(f"[Dev] Dispatched render job {job_id} to Celery queue (task ID: {task.id})")
            return "celery", str(task.id)
        except Exception as exc:
            logger.warning(f"[Dev] Celery broker unreachable ({exc}); using in-process background execution for local development.")

    if background_tasks is not None:
        background_tasks.add_task(RenderService.execute_render_background, job_id, project_id, user_id)
    else:
        asyncio.create_task(RenderService.execute_render_background(job_id, project_id, user_id))
    return "background_task", None

