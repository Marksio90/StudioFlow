import uuid
from collections.abc import AsyncGenerator
import os

from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.repositories.video_project_repository import DBVideoProjectRepository
from app.services.video_project_service import VideoProjectService
from app.services.usage_service import UsageService


def _parse_api_keys_env() -> dict[str, str]:
    raw = os.getenv("AUTH_API_KEYS", "")
    pairs = [item.strip() for item in raw.split(",") if item.strip()]
    key_roles: dict[str, str] = {}
    for pair in pairs:
        key, sep, role = pair.partition(":")
        if not sep:
            continue
        key_roles[key.strip()] = role.strip().lower()
    return key_roles


def require_mutation_auth(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    key_roles = _parse_api_keys_env()
    if not key_roles:
        return
    if not x_api_key or x_api_key not in key_roles:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if key_roles[x_api_key] not in {"editor", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


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
