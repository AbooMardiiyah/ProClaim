"""
ProClaim — Celery Application
Async task queue backed by Redis. Workers run extraction tasks independently
of the FastAPI request lifecycle.
"""
from celery import Celery
from celery.signals import worker_ready

from app.config import settings

celery_app = Celery(
    "proclaim",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                # Re-queue on worker crash
    worker_prefetch_multiplier=1,       # One task at a time per worker for heavy extraction
    task_routes={
        "app.workers.tasks.extract_documents": {"queue": "extraction"},
    },
    beat_schedule={},
)


@worker_ready.connect
def on_worker_ready(sender, **kwargs):  # type: ignore[no-untyped-def]
    import structlog
    log = structlog.get_logger()
    log.info("celery.worker_ready", broker=settings.CELERY_BROKER_URL)
