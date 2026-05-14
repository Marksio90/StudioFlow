"""Workflow worker entrypoints for video production pipeline (MVP placeholders)."""

from uuid import UUID

from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.video_project_service import VideoProjectService
from apps.worker.worker_app import celery_app

repo_singleton = InMemoryVideoProjectRepository()


def get_video_project_service() -> VideoProjectService:
    return VideoProjectService(repo_singleton)


@celery_app.task(name="workflow.video.start")
def start_video_workflow(video_project_id: str) -> dict:
    return {"video_project_id": video_project_id, "state": "queued"}


@celery_app.task(name="workflow.video.sync_analytics")
def sync_analytics(video_project_id: str, youtube_video_id: str) -> dict:
    return {"video_project_id": video_project_id, "youtube_video_id": youtube_video_id, "state": "synced"}


@celery_app.task(name="workflow.video.publish")
def publish_video(publishing_plan_id: str) -> dict:
    service = get_video_project_service()
    result = service.publish_video(UUID(publishing_plan_id))
    return {"publishing_plan_id": publishing_plan_id, "status": result["status"], "youtube_video_id": result.get("youtube_video_id")}
