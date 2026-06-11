from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "logo_promotion_saas",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.filter_tasks",
        "app.workers.tasks.pipeline_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        # Dedicated queues so worker pools can be scaled independently per
        # stage (e.g. more upload workers than submission workers).
        "app.workers.tasks.filter_tasks.*": {"queue": "filter"},
        "app.workers.tasks.pipeline_tasks.download_reel": {"queue": "download"},
        "app.workers.tasks.pipeline_tasks.edit_reel": {"queue": "edit"},
        "app.workers.tasks.pipeline_tasks.upload_reel": {"queue": "upload"},
        "app.workers.tasks.pipeline_tasks.submit_to_clipster": {"queue": "submit"},
    },
    beat_schedule={
        "dispatch-due-queue-items": {
            "task": "app.workers.tasks.pipeline_tasks.dispatch_due_items",
            "schedule": 30.0,
        },
        "cleanup-old-logs": {
            "task": "app.workers.tasks.pipeline_tasks.cleanup_old_logs",
            "schedule": 3600.0,
        },
    },
)
