from celery import Task, Celery
from api import create_worker_app

class FlaskTask(Task):
    _flask_app = None

    @property
    def flask_app(self):
        """懒加载——每个 Worker 进程只创建一次 Flask 实例"""
        if self._flask_app is None:
            self._flask_app = create_worker_app()
        return self._flask_app

    def __call__(self, *args, **kwargs):
        with self.flask_app.app_context():
            return super().__call__(*args, **kwargs)

celery = Celery("govrag", broker="redis://:redis123@localhost:6379/1", task_cls="api.celery_app.FlaskTask")

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=['api.tasks.document_tasks'], 
)

