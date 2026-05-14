from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


DEFAULT_YOUTUBE_METHOD_COSTS: dict[str, int] = {
    "videos.insert": 1600,
    "videos.update": 50,
    "videos.list": 1,
    "search.list": 100,
    "captions.insert": 400,
    "thumbnails.set": 50,
}


@dataclass
class YouTubeCallContext:
    organization_id: UUID
    workspace_id: UUID
    channel_id: UUID
    video_project_id: UUID | None = None
    workflow_run_id: UUID | None = None


class YouTubeQuotaService:
    def __init__(self, repo, method_costs: dict[str, int] | None = None):
        self.repo = repo
        self.method_costs = method_costs or DEFAULT_YOUTUBE_METHOD_COSTS.copy()

    def resolve_cost(self, youtube_method: str) -> int:
        return self.method_costs.get(youtube_method, 1)

    def log_call(
        self,
        context: YouTubeCallContext,
        youtube_method: str,
        success: bool,
        retry_of_id: UUID | None = None,
        quota_cost: int | None = None,
    ):
        entry = {
            "organization_id": context.organization_id,
            "workspace_id": context.workspace_id,
            "channel_id": context.channel_id,
            "video_project_id": context.video_project_id,
            "workflow_run_id": context.workflow_run_id,
            "youtube_method": youtube_method,
            "quota_cost": quota_cost if quota_cost is not None else self.resolve_cost(youtube_method),
            "success": success,
            "retry_of_id": retry_of_id,
            "created_at": datetime.now(timezone.utc),
        }
        return self.repo.log_youtube_quota_entry(entry)


class YouTubeClientQuotaWrapper:
    def __init__(self, client, quota_service: YouTubeQuotaService):
        self.client = client
        self.quota_service = quota_service

    def call(self, youtube_method: str, context: YouTubeCallContext, retry_of_id: UUID | None = None, **kwargs):
        try:
            result = self.client.call(youtube_method, **kwargs)
            self.quota_service.log_call(context, youtube_method, success=True, retry_of_id=retry_of_id)
            return result
        except Exception:
            self.quota_service.log_call(context, youtube_method, success=False, retry_of_id=retry_of_id)
            raise
