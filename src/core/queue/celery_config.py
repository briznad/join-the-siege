from celery import Celery
from celery.schedules import crontab
from ..config import get_settings

settings = get_settings()

celery_app = Celery(
    'document_classifier',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    task_routes={
        'document_classifier.tasks.classify_document': {'queue': 'classification'},
        'document_classifier.tasks.extract_text': {'queue': 'extraction'}
    },
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    enable_utc=True,
    timezone='UTC',
    broker_connection_retry_on_startup=True,
    broker_pool_limit=None,
    result_expires=3600,
    worker_concurrency=settings.WORKER_CONCURRENCY,
    worker_max_memory_per_child=200000,
    task_annotations={
        '*': {
            'rate_limit': '100/s'
        }
    },
    beat_schedule={
        'cleanup-expired-documents': {
            'task': 'document_classifier.tasks.cleanup_expired_documents',
            'schedule': crontab(hour=0, minute=0)
        },
        'monitor-queue-sizes': {
            'task': 'document_classifier.tasks.monitor_queue_sizes',
            'schedule': 60.0
        }
    }
)
