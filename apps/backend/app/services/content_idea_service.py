from __future__ import annotations

from uuid import UUID


class ContentIdeaService:
    """Service facade for content ideas with deprecated VideoIdea wrappers."""

    def __init__(self, repository) -> None:
        self.repository = repository

    async def create_content_idea(self, payload: dict):
        return await self.repository.create_content_idea(payload)

    async def get_content_idea(self, idea_id: UUID):
        return await self.repository.get_content_idea(idea_id)

    async def update_content_idea(self, idea_id: UUID, payload: dict):
        return await self.repository.update_content_idea(idea_id, payload)

    async def delete_content_idea(self, idea_id: UUID):
        return await self.repository.delete_content_idea(idea_id)

    async def set_content_idea_status(self, idea_id: UUID, status: str):
        return await self.repository.set_content_idea_status(idea_id, status)

    async def list_content_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ):
        return await self.repository.list_content_ideas(channel_id, status, content_pillar, q, include_archived)

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict):
        return await self.create_content_idea(payload)

    async def get_video_idea(self, idea_id: UUID):
        return await self.get_content_idea(idea_id)

    async def update_video_idea(self, idea_id: UUID, payload: dict):
        return await self.update_content_idea(idea_id, payload)

    async def delete_video_idea(self, idea_id: UUID):
        return await self.delete_content_idea(idea_id)

    async def set_video_idea_status(self, idea_id: UUID, status: str):
        return await self.set_content_idea_status(idea_id, status)

    async def list_video_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ):
        return await self.list_content_ideas(channel_id, status, content_pillar, q, include_archived)
