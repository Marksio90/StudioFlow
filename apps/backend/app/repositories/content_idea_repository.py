from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContentIdea


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryContentIdeaRepository:
    """Content-idea repository with VideoIdea compatibility wrappers."""

    def __init__(self) -> None:
        self._ideas: dict[UUID, dict] = {}

    async def create_content_idea(self, payload: dict) -> dict:
        row = {"id": _uuid.uuid4(), "created_at": _now(), "updated_at": _now(), **payload}
        self._ideas[row["id"]] = row
        return dict(row)

    async def list_content_ideas(self, project_id: UUID) -> list[dict]:
        rows = [r for r in self._ideas.values() if r.get("video_project_id") == project_id]
        return sorted((dict(r) for r in rows), key=lambda r: r["created_at"])

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict) -> dict:
        return await self.create_content_idea(payload)

    async def list_video_ideas(self, project_id: UUID) -> list[dict]:
        return await self.list_content_ideas(project_id)


class ContentIdeaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_content_idea(self, payload: dict) -> ContentIdea:
        row = ContentIdea(**payload)
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def list_content_ideas(self, project_id: UUID) -> list[ContentIdea]:
        stmt = select(ContentIdea).where(ContentIdea.video_project_id == project_id).order_by(ContentIdea.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict) -> ContentIdea:
        return await self.create_content_idea(payload)

    async def list_video_ideas(self, project_id: UUID) -> list[ContentIdea]:
        return await self.list_content_ideas(project_id)
