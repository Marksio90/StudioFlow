from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
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

    async def get_content_idea(self, idea_id: UUID) -> dict | None:
        row = self._ideas.get(idea_id)
        return dict(row) if row is not None else None

    async def update_content_idea(self, idea_id: UUID, payload: dict) -> dict | None:
        row = self._ideas.get(idea_id)
        if row is None:
            return None
        for key, value in payload.items():
            if value is not None:
                row[key] = value
        row["updated_at"] = _now()
        return dict(row)

    async def delete_content_idea(self, idea_id: UUID) -> bool:
        if idea_id not in self._ideas:
            return False
        del self._ideas[idea_id]
        return True

    async def set_content_idea_status(self, idea_id: UUID, status: str) -> dict | None:
        return await self.update_content_idea(idea_id, {"status": status})

    async def list_content_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        rows = [r for r in self._ideas.values() if r.get("channel_id") == channel_id]
        if status is not None:
            rows = [r for r in rows if r.get("status") == status]
        if content_pillar is not None:
            rows = [r for r in rows if r.get("content_pillar") == content_pillar]
        if not include_archived:
            rows = [r for r in rows if r.get("status") != "archived"]
        if q:
            needle = q.lower().strip()
            rows = [
                r
                for r in rows
                if needle in (r.get("title", "") + " " + r.get("description", "") + " " + r.get("notes", "")).lower()
            ]
        return sorted((dict(r) for r in rows), key=lambda r: r["created_at"])

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict) -> dict:
        return await self.create_content_idea(payload)

    async def get_video_idea(self, idea_id: UUID) -> dict | None:
        return await self.get_content_idea(idea_id)

    async def update_video_idea(self, idea_id: UUID, payload: dict) -> dict | None:
        return await self.update_content_idea(idea_id, payload)

    async def delete_video_idea(self, idea_id: UUID) -> bool:
        return await self.delete_content_idea(idea_id)

    async def set_video_idea_status(self, idea_id: UUID, status: str) -> dict | None:
        return await self.set_content_idea_status(idea_id, status)

    async def list_video_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        return await self.list_content_ideas(channel_id, status, content_pillar, q, include_archived)


class ContentIdeaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_content_idea(self, payload: dict) -> ContentIdea:
        row = ContentIdea(**payload)
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def get_content_idea(self, idea_id: UUID) -> ContentIdea | None:
        stmt = select(ContentIdea).where(ContentIdea.id == idea_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_content_idea(self, idea_id: UUID, payload: dict) -> ContentIdea | None:
        row = await self.get_content_idea(idea_id)
        if row is None:
            return None
        for key, value in payload.items():
            if value is not None:
                setattr(row, key, value)
        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def delete_content_idea(self, idea_id: UUID) -> bool:
        row = await self.get_content_idea(idea_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        return True

    async def set_content_idea_status(self, idea_id: UUID, status: str) -> ContentIdea | None:
        return await self.update_content_idea(idea_id, {"status": status})

    async def list_content_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ) -> list[ContentIdea]:
        stmt = select(ContentIdea).where(ContentIdea.channel_id == channel_id)
        if status is not None:
            stmt = stmt.where(ContentIdea.status == status)
        if content_pillar is not None:
            stmt = stmt.where(ContentIdea.content_pillar == content_pillar)
        if not include_archived:
            stmt = stmt.where(ContentIdea.status != "archived")
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(or_(ContentIdea.title.ilike(pattern), ContentIdea.description.ilike(pattern), ContentIdea.notes.ilike(pattern)))
        stmt = stmt.order_by(ContentIdea.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # Deprecated wrappers.
    async def create_video_idea(self, payload: dict) -> ContentIdea:
        return await self.create_content_idea(payload)

    async def get_video_idea(self, idea_id: UUID) -> ContentIdea | None:
        return await self.get_content_idea(idea_id)

    async def update_video_idea(self, idea_id: UUID, payload: dict) -> ContentIdea | None:
        return await self.update_content_idea(idea_id, payload)

    async def delete_video_idea(self, idea_id: UUID) -> bool:
        return await self.delete_content_idea(idea_id)

    async def set_video_idea_status(self, idea_id: UUID, status: str) -> ContentIdea | None:
        return await self.set_content_idea_status(idea_id, status)

    async def list_video_ideas(
        self,
        channel_id: UUID,
        status: str | None = None,
        content_pillar: str | None = None,
        q: str | None = None,
        include_archived: bool = False,
    ) -> list[ContentIdea]:
        return await self.list_content_ideas(channel_id, status, content_pillar, q, include_archived)
