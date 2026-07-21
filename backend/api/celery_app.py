from celery import Celery

celery = Celery("govrag", broker="redis://:redis123@localhost:6379/1")

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=['api.tasks.document_tasks'], 
)

