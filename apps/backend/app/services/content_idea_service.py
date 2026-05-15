from __future__ import annotations

from uuid import UUID


class ContentIdeaService:
    """Service facade for content ideas with deprecated VideoIdea wrappers."""

    def __init__(self, repository) -> None:
        self.repository = repository

    async def create_content_idea(self, payload: dict):
        return await self.repository.create_content_idea(payload)

    async def list_content_ideas(self, project_id: UUID):
        return await self.repository.list_content_ideas(project_id)

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict):
        return await self.create_content_idea(payload)

    async def list_video_ideas(self, project_id: UUID):
        return await self.list_content_ideas(project_id)
