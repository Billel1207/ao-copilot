from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "aocopilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24h
    beat_schedule={
        # Veille BOAMP — toutes les heures
        "sync_boamp_all_orgs": {
            "task": "sync_boamp_all_orgs",
            "schedule": 3600,  # secondes
        },
        # Rappels deadline J-7 — tous les jours à 8h Europe/Paris
        "send_daily_deadline_reminders": {
            "task": "send_daily_deadline_reminders",
            "schedule": crontab(hour=8, minute=0),
        },
        # Purge rétention — tous les jours à 3h du matin
        "purge_expired_data": {
            "task": "purge_expired_data",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
