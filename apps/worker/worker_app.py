from celery import Celery

celery_app = Celery(
    "ai_media_ops_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

import apps.worker.app.tasks.video_workflow  # noqa: E402,F401


@celery_app.task(name="worker.ping")
def ping() -> str:
    return "pong"
