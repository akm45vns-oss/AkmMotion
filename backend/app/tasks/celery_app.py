from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "akmmotion_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.RENDER_TIMEOUT_SECONDS,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    imports=["app.tasks.video_tasks"]
)

