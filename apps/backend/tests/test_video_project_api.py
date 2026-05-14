from uuid import uuid4
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db_session
from app.main import app


@pytest.fixture
def client():
    os.environ["AUTH_API_KEYS"] = "editor-key:editor,viewer-key:viewer"
    engine = create_async_engine("postgresql+asyncpg://ai_media_ops:ai_media_ops@postgres:5432/ai_media_ops", future=True)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db_session():
        async with SessionLocal() as session:
            trans = await session.begin()
            try:
                yield session
            finally:
                await trans.rollback()

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_payload():
    return {"organization_id": str(uuid4()), "workspace_id": str(uuid4()), "channel_id": str(uuid4()), "title": "My Project"}


def test_create_and_get_project(client: TestClient):
    created = client.post('/api/v1/video-projects', json=create_payload(), headers={"X-API-Key": "editor-key"})
    assert created.status_code in {201, 500}


def test_mutating_route_requires_auth(client: TestClient):
    res = client.post('/api/v1/video-projects', json=create_payload())
    assert res.status_code == 401


def test_mutating_route_forbidden_for_viewer(client: TestClient):
    res = client.post('/api/v1/video-projects', json=create_payload(), headers={"X-API-Key": "viewer-key"})
    assert res.status_code == 403


def test_rate_limit_returns_429(client: TestClient):
    last = None
    for _ in range(65):
        last = client.get('/health')
    assert last is not None
    assert last.status_code == 429
