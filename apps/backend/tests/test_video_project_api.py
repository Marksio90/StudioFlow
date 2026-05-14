from uuid import uuid4
import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
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


def _tenant_headers(role_key: str = "editor-key", org_id: str | None = None, workspace_id: str | None = None):
    return {"X-API-Key": role_key, "X-Org-Id": org_id or "00000000-0000-0000-0000-000000000001", "X-Workspace-Id": workspace_id or "00000000-0000-0000-0000-000000000001", "X-User-Id": "00000000-0000-0000-0000-000000000011"}


def _create_project(client: TestClient):
    payload = create_payload()
    payload["organization_id"] = "00000000-0000-0000-0000-000000000001"
    payload["workspace_id"] = "00000000-0000-0000-0000-000000000001"
    res = client.post('/api/v1/video-projects', json=payload, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def _create_plan(client: TestClient, project: dict):
    res = client.post('/api/v1/video-projects/publishing-plans', json={
        "video_project_id": project["id"],
        "channel_id": project["channel_id"],
        "title": "Plan title",
        "description": "Desc",
        "tags": ["a"],
        "visibility": "private",
    }, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def test_create_and_get_project(client: TestClient):
    created = _create_project(client)
    assert created["id"]


def test_mutating_route_requires_auth(client: TestClient):
    res = client.post('/api/v1/video-projects', json=create_payload())
    assert res.status_code == 401


def test_mutating_route_forbidden_for_viewer(client: TestClient):
    res = client.post('/api/v1/video-projects', json=create_payload(), headers=_tenant_headers("viewer-key"))
    assert res.status_code == 403


def test_rate_limit_returns_429(client: TestClient):
    last = None
    for _ in range(65):
        last = client.get('/health')
    assert last is not None
    assert last.status_code == 429


def test_publish_flow_success(client: TestClient):
    project = _create_project(client)
    project_id = project["id"]

    req = client.post(f'/api/v1/video-projects/{project_id}/request-approval', headers=_tenant_headers())
    assert req.status_code == 200

    approve = client.post(f'/api/v1/video-projects/{project_id}/approve', json={"comment": "ok", "decided_by_user_id": str(uuid4())}, headers=_tenant_headers())
    assert approve.status_code == 200

    compliance = client.post(f'/api/v1/video-projects/{project_id}/compliance', json={"metadata": {}, "disclosure_decision_missing": False}, headers=_tenant_headers())
    assert compliance.status_code == 200

    plan = _create_plan(client, project)
    plan_id = plan["id"]

    schedule = client.post(f'/api/v1/video-projects/publishing-plans/{plan_id}/schedule', json={"scheduled_at": datetime.now(timezone.utc).isoformat()}, headers=_tenant_headers())
    assert schedule.status_code == 200, schedule.text
    assert schedule.json()["status"] == "scheduled"

    publish = client.post(f'/api/v1/video-projects/publishing-plans/{plan_id}/publish', headers=_tenant_headers())
    assert publish.status_code == 200, publish.text
    assert publish.json()["status"] == "published"


def test_publish_flow_blocked(client: TestClient):
    project = _create_project(client)
    project_id = project["id"]

    client.post(f'/api/v1/video-projects/{project_id}/request-approval', headers=_tenant_headers())
    reject = client.post(f'/api/v1/video-projects/{project_id}/reject', json={"comment": "no", "decided_by_user_id": str(uuid4())}, headers=_tenant_headers())
    assert reject.status_code == 200

    plan = _create_plan(client, project)
    schedule = client.post(f'/api/v1/video-projects/publishing-plans/{plan["id"]}/schedule', json={"scheduled_at": datetime.now(timezone.utc).isoformat()}, headers=_tenant_headers())
    assert schedule.status_code == 409


def test_cross_tenant_project_access_forbidden(client: TestClient):
    project = _create_project(client)
    res = client.get(f"/api/v1/video-projects/{project['id']}", headers=_tenant_headers(org_id=str(uuid4()), workspace_id=str(uuid4())))
    assert res.status_code == 403


def test_cross_tenant_usage_access_forbidden(client: TestClient):
    org_id = "00000000-0000-0000-0000-000000000001"
    res = client.get(f"/api/v1/usage/{org_id}", headers=_tenant_headers(org_id=str(uuid4())))
    assert res.status_code == 403


def test_publish_requires_approved_status_even_if_scheduled(client: TestClient):
    project = _create_project(client)
    plan = _create_plan(client, project)

    force_schedule = client.post(
        f"/api/v1/video-projects/publishing-plans/{plan['id']}/schedule",
        json={"scheduled_at": datetime.now(timezone.utc).isoformat()},
        headers=_tenant_headers(),
    )
    assert force_schedule.status_code == 409


def test_publish_requires_non_blocked_compliance(client: TestClient):
    project = _create_project(client)
    project_id = project["id"]

    req = client.post(f'/api/v1/video-projects/{project_id}/request-approval', headers=_tenant_headers())
    assert req.status_code == 200

    approve = client.post(f'/api/v1/video-projects/{project_id}/approve', json={"comment": "ok", "decided_by_user_id": str(uuid4())}, headers=_tenant_headers())
    assert approve.status_code == 200

    compliance = client.post(
        f'/api/v1/video-projects/{project_id}/compliance',
        json={"metadata": {"asset_license_risk": "high", "score": 99}, "disclosure_decision_missing": True},
        headers=_tenant_headers(),
    )
    assert compliance.status_code == 200

    plan = _create_plan(client, project)
    schedule = client.post(
        f"/api/v1/video-projects/publishing-plans/{plan['id']}/schedule",
        json={"scheduled_at": datetime.now(timezone.utc).isoformat()},
        headers=_tenant_headers(),
    )
    assert schedule.status_code == 409
