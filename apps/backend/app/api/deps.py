import logging
import os
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.observability import correlation_id_var
from app.repositories.video_project_repository import DBVideoProjectRepository, InMemoryVideoProjectRepository
from app.services.ai_provider import LLMProvider, MockLLMProvider, OllamaProvider, OpenAICompatibleProvider
from app.services.usage_service import UsageService
from app.services.video_project_service import VideoProjectService

logger = logging.getLogger("app.authz")

ROLE_MATRIX: dict[str, set[str]] = {
    "viewer": {"read"},
    "editor": {"read", "write"},
    "admin": {"read", "write", "manage"},
    "owner": {"read", "write", "manage", "owner"},
}

# Singleton in-memory repo used when DATABASE_URL is not configured (dev/unit-test mode).
repo_singleton = InMemoryVideoProjectRepository()


@dataclass(frozen=True)
class Identity:
    user_id: UUID
    org_id: UUID
    workspace_id: UUID
    role: str
    dev_mode: bool = field(default=False)


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


def get_correlation_id(x_correlation_id: str | None = Header(default=None)) -> str:
    correlation_id = x_correlation_id or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def _audit_authz(identity: Identity | None, decision: str, reason: str, correlation_id: str, action: str, resource: str) -> None:
    logger.info(
        "authz decision=%s reason=%s correlation_id=%s action=%s resource=%s identity=%s",
        decision,
        reason,
        correlation_id,
        action,
        resource,
        identity,
    )


def get_identity(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
    x_org_id: UUID | None = Header(default=None, alias="X-Org-Id"),
    x_workspace_id: UUID | None = Header(default=None, alias="X-Workspace-Id"),
    correlation_id: str = Depends(get_correlation_id),
) -> Identity:
    key_roles = _parse_api_keys_env()
    dev_mode = not key_roles
    if key_roles:
        if not x_api_key or x_api_key not in key_roles:
            _audit_authz(None, "deny", "invalid_api_key", correlation_id, "authenticate", "identity")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        role = key_roles[x_api_key]
    else:
        role = "owner"

    if role not in ROLE_MATRIX:
        _audit_authz(None, "deny", "unknown_role", correlation_id, "authenticate", "identity")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    identity = Identity(
        user_id=x_user_id or UUID("00000000-0000-0000-0000-000000000001"),
        org_id=x_org_id or UUID("00000000-0000-0000-0000-000000000001"),
        workspace_id=x_workspace_id or UUID("00000000-0000-0000-0000-000000000001"),
        role=role,
        dev_mode=dev_mode,
    )
    _audit_authz(identity, "allow", "authenticated", correlation_id, "authenticate", "identity")
    return identity


def require_action(action: str, resource: str):
    def dependency(identity: Identity = Depends(get_identity), correlation_id: str = Depends(get_correlation_id)) -> Identity:
        if action not in ROLE_MATRIX.get(identity.role, set()):
            _audit_authz(identity, "deny", "role_not_allowed", correlation_id, action, resource)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        _audit_authz(identity, "allow", "role_allowed", correlation_id, action, resource)
        return identity

    return dependency


async def get_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    if not os.getenv("DATABASE_URL"):
        yield None
        return
    async with AsyncSessionLocal() as session:
        yield session


def get_video_project_service(session: AsyncSession | None = Depends(get_db_session)) -> VideoProjectService:
    repo = DBVideoProjectRepository(session) if session is not None else repo_singleton
    return VideoProjectService(repo, usage_service=UsageService(repo))


def get_usage_service(session: AsyncSession | None = Depends(get_db_session)) -> UsageService:
    repo = DBVideoProjectRepository(session) if session is not None else repo_singleton
    return UsageService(repo)


def get_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    if provider == "mock":
        return MockLLMProvider()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaProvider(model=model, base_url=base_url)

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if base_url and api_key and model:
        return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)

    env = os.getenv("APP_ENV", os.getenv("ENV", "")).strip().lower()
    if env in {"local", "development", "dev", "test"}:
        return MockLLMProvider()

    return MockLLMProvider()
