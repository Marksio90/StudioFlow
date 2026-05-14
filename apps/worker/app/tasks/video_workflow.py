"""Workflow worker entrypoints for video production pipeline."""

import asyncio
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.repositories.video_project_repository import DBVideoProjectRepository
from app.services.video_project_service import VideoProjectService
from app.services.workflow_events import WorkflowEventEmitter
from apps.worker.worker_app import celery_app
from app.observability import TraceContext, metrics, correlation_id_var

NON_RETRYABLE_ERRORS = {ValueError}


async def _run_publish_video(publishing_plan_id: str, correlation_id: str | None = None) -> dict:
    async with AsyncSessionLocal() as session:
        repo = DBVideoProjectRepository(session)
        service = VideoProjectService(repo)
        event_emitter = WorkflowEventEmitter(repo)
        business_key = f"{publishing_plan_id}:publish_video"
        execution = await repo.get_or_create_task_execution("publish_video", business_key, business_key)
        correlation_id_var.set(correlation_id)
        if execution.status == "succeeded":
            return {"publishing_plan_id": publishing_plan_id, "status": "published", "deduplicated": True}
        attempt_no = execution.retry_count + 1
        await repo.add_task_attempt(execution.id, attempt_no, "running")
        try:
            result = await service.publish_video(UUID(publishing_plan_id))
            await repo.mark_task_execution(execution.id, "succeeded", execution.retry_count)
            await repo.add_task_attempt(execution.id, attempt_no, "succeeded")
            await event_emitter.emit(result["video_project_id"], None, "task.publish_video.succeeded", {"publishing_plan_id": publishing_plan_id}, correlation_id=correlation_id, task_id=str(execution.id))
            return {"publishing_plan_id": publishing_plan_id, "status": result["status"], "youtube_video_id": result.get("youtube_video_id")}
        except Exception as exc:
            metrics.inc("publish_failures", 1)
            await repo.mark_task_execution(execution.id, "failed", execution.retry_count + 1, error_code=type(exc).__name__)
            await repo.add_task_attempt(execution.id, attempt_no, "failed", error_code=type(exc).__name__)
            raise


async def _run_sync_analytics(video_project_id: str, youtube_video_id: str, correlation_id: str | None = None) -> dict:
    async with AsyncSessionLocal() as session:
        repo = DBVideoProjectRepository(session)
        event_emitter = WorkflowEventEmitter(repo)
        business_key = f"{video_project_id}:{youtube_video_id}:sync_analytics"
        execution = await repo.get_or_create_task_execution("sync_analytics", business_key, business_key)
        correlation_id_var.set(correlation_id)
        if execution.status == "succeeded":
            return {"video_project_id": video_project_id, "youtube_video_id": youtube_video_id, "state": "synced", "deduplicated": True}
        attempt_no = execution.retry_count + 1
        await repo.add_task_attempt(execution.id, attempt_no, "running")
        try:
            await repo.mark_task_execution(execution.id, "succeeded", execution.retry_count)
            await repo.add_task_attempt(execution.id, attempt_no, "succeeded")
            await event_emitter.emit(UUID(video_project_id), None, "task.sync_analytics.succeeded", {"youtube_video_id": youtube_video_id}, correlation_id=correlation_id)
            return {"video_project_id": video_project_id, "youtube_video_id": youtube_video_id, "state": "synced"}
        except Exception as exc:
            metrics.inc("publish_failures", 1)
            await repo.mark_task_execution(execution.id, "failed", execution.retry_count + 1, error_code=type(exc).__name__)
            await repo.add_task_attempt(execution.id, attempt_no, "failed", error_code=type(exc).__name__)
            raise


@celery_app.task(name="workflow.video.start")
def start_video_workflow(video_project_id: str) -> dict:
    return {"video_project_id": video_project_id, "state": "queued"}


@celery_app.task(
    name="workflow.video.sync_analytics",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def sync_analytics(self, video_project_id: str, youtube_video_id: str, correlation_id: str | None = None) -> dict:
    with TraceContext(correlation_id or f"sync-{video_project_id}"):
        try:
            return asyncio.run(_run_sync_analytics(video_project_id, youtube_video_id, correlation_id=correlation_id))
        except Exception as exc:
            if type(exc) in NON_RETRYABLE_ERRORS:
                raise
            raise self.retry(exc=exc)


@celery_app.task(
    name="workflow.video.publish",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def publish_video(self, publishing_plan_id: str, correlation_id: str | None = None) -> dict:
    with TraceContext(correlation_id or f"publish-{publishing_plan_id}"):
        try:
            return asyncio.run(_run_publish_video(publishing_plan_id, correlation_id=correlation_id))
        except Exception as exc:
            if type(exc) in NON_RETRYABLE_ERRORS:
                raise
            raise self.retry(exc=exc)
