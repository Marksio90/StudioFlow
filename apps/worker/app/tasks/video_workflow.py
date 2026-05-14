"""Workflow worker entrypoints for video production pipeline (MVP placeholders)."""

from worker_app import celery_app


@celery_app.task(name="workflow.video.start")
def start_video_workflow(video_project_id: str) -> dict:
    return {"video_project_id": video_project_id, "state": "queued"}


@celery_app.task(name="workflow.video.sync_analytics")
def sync_analytics(video_project_id: str, youtube_video_id: str) -> dict:
    return {"video_project_id": video_project_id, "youtube_video_id": youtube_video_id, "state": "synced"}
