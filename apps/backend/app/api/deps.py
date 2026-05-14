import uuid
from fastapi import Header

from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.video_project_service import VideoProjectService
from app.services.usage_service import UsageService

repo_singleton = InMemoryVideoProjectRepository()


def get_correlation_id(x_correlation_id: str | None = Header(default=None)) -> str:
    return x_correlation_id or str(uuid.uuid4())


def get_video_project_service() -> VideoProjectService:
    return VideoProjectService(repo_singleton)


def get_usage_service() -> UsageService:
    return UsageService(repo_singleton)
