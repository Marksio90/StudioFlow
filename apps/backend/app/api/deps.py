import uuid
from collections.abc import AsyncGenerator

from fastapi import Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.repositories.video_project_repository import DBVideoProjectRepository
from app.services.video_project_service import VideoProjectService
from app.services.usage_service import UsageService


def get_correlation_id(x_correlation_id: str | None = Header(default=None)) -> str:
    return x_correlation_id or str(uuid.uuid4())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_video_project_service(session: AsyncSession = Depends(get_db_session)) -> VideoProjectService:
    repo = DBVideoProjectRepository(session)
    return VideoProjectService(repo)


def get_usage_service(session: AsyncSession = Depends(get_db_session)) -> UsageService:
    return UsageService(DBVideoProjectRepository(session))
