from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "brainybuddy",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "poll-google-calendar-changes": {
        "task": "app.tasks.sync_tasks.poll_google_calendar_changes",
        "schedule": crontab(minute="*/5"),
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
