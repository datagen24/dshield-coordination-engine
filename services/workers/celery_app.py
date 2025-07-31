"""Celery application configuration for background task processing."""

from celery import Celery
from celery.schedules import crontab

from services.api.config import settings

# Create Celery app
celery_app = Celery(
    "dshield_coordination_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["services.workers.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
    task_ignore_result=False,
    task_always_eager=settings.debug,  # Run synchronously in debug mode
)

# Configure task routes
celery_app.conf.task_routes = {
    "services.workers.tasks.analyze_coordination_task": {"queue": "coordination"},
    "services.workers.tasks.process_bulk_analysis_task": {"queue": "bulk"},
    "services.workers.tasks.enrich_attack_sessions_task": {"queue": "enrichment"},
}

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-results": {
        "task": "services.workers.tasks.cleanup_expired_results_task",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "health-check": {
        "task": "services.workers.tasks.health_check_task",
        "schedule": 300.0,  # Every 5 minutes
    },
}

# Configure task annotations
celery_app.conf.task_annotations = {
    "services.workers.tasks.analyze_coordination_task": {
        "rate_limit": "10/m",  # 10 tasks per minute
        "max_retries": 3,
        "default_retry_delay": 60,
    },
    "services.workers.tasks.process_bulk_analysis_task": {
        "rate_limit": "5/m",  # 5 tasks per minute
        "max_retries": 3,
        "default_retry_delay": 120,
    },
    "services.workers.tasks.enrich_attack_sessions_task": {
        "rate_limit": "20/m",  # 20 tasks per minute
        "max_retries": 2,
        "default_retry_delay": 30,
    },
}

if __name__ == "__main__":
    celery_app.start()
