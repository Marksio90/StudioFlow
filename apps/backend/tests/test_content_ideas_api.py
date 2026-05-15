import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_usage_service, get_video_project_service
from app.main import app
from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.usage_service import UsageService
from app.services.video_project_service import VideoProjectService


@pytest.fixture
def client():
    os.environ["AUTH_API_KEYS"] = "editor-key:editor,viewer-key:viewer"
    test_repo = InMemoryVideoProjectRepository()

    def override_service():
        return VideoProjectService(test_repo, usage_service=UsageService(test_repo))

    def override_usage():
        return UsageService(test_repo)

    app.dependency_overrides[get_video_project_service] = override_service
    app.dependency_overrides[get_usage_service] = override_usage
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_API_KEYS", None)


def _tenant_headers(role_key: str = "editor-key"):
    return {
        "X-API-Key": role_key,
        "X-Org-Id": "00000000-0000-0000-0000-000000000001",
        "X-Workspace-Id": "00000000-0000-0000-0000-000000000001",
        "X-User-Id": "00000000-0000-0000-0000-000000000011",
    }


def _create_channel(client: TestClient) -> dict:
    payload = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "name": "Ideas Channel",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def _idea_payload(channel_id: str, **overrides):
    payload = {
        "video_project_id": str(uuid4()),
        "channel_id": channel_id,
        "title": "Core idea",
        "description": "Base description",
        "status": "idea",
        "content_pillar": "education",
        "notes": "baseline notes",
    }
    payload.update(overrides)
    return payload


def test_content_ideas_crud_and_filtering_semantics(client: TestClient):
    channel = _create_channel(client)
    channel_id = channel["id"]

    first = client.post(f"/api/v1/channels/{channel_id}/ideas", json=_idea_payload(channel_id, title="Alpha", content_pillar="news", description="market pulse"), headers=_tenant_headers())
    second = client.post(f"/api/v1/channels/{channel_id}/ideas", json=_idea_payload(channel_id, title="Beta", content_pillar="education", description="deep dive"), headers=_tenant_headers())
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    first_id = first.json()["id"]

    fetched = client.get(f"/api/v1/ideas/{first_id}", headers=_tenant_headers())
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Alpha"

    patched = client.patch(f"/api/v1/ideas/{first_id}", json={"title": "Alpha Updated", "content_pillar": "news"}, headers=_tenant_headers())
    assert patched.status_code == 200
    assert patched.json()["title"] == "Alpha Updated"

    filtered_by_pillar = client.get(f"/api/v1/channels/{channel_id}/ideas", params={"content_pillar": "education"}, headers=_tenant_headers())
    assert filtered_by_pillar.status_code == 200
    assert [row["title"] for row in filtered_by_pillar.json()] == ["Beta"]

    filtered_by_q = client.get(f"/api/v1/channels/{channel_id}/ideas", params={"q": "market"}, headers=_tenant_headers())
    assert filtered_by_q.status_code == 200
    assert [row["title"] for row in filtered_by_q.json()] == ["Alpha Updated"]

    deleted = client.delete(f"/api/v1/ideas/{first_id}", headers=_tenant_headers())
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/ideas/{first_id}", headers=_tenant_headers())
    assert missing.status_code == 404


def test_archived_ideas_excluded_by_default_and_included_with_override(client: TestClient):
    channel = _create_channel(client)
    channel_id = channel["id"]

    active = client.post(f"/api/v1/channels/{channel_id}/ideas", json=_idea_payload(channel_id, title="Active", status="idea"), headers=_tenant_headers())
    archived = client.post(f"/api/v1/channels/{channel_id}/ideas", json=_idea_payload(channel_id, title="Archived", status="archived"), headers=_tenant_headers())
    assert active.status_code == 201
    assert archived.status_code == 201

    default_list = client.get(f"/api/v1/channels/{channel_id}/ideas", headers=_tenant_headers())
    assert default_list.status_code == 200
    assert [row["title"] for row in default_list.json()] == ["Active"]

    with_archived = client.get(f"/api/v1/channels/{channel_id}/ideas", params={"include_archived": True}, headers=_tenant_headers())
    assert with_archived.status_code == 200
    assert {row["title"] for row in with_archived.json()} == {"Active", "Archived"}


def test_invalid_status_is_rejected_for_create_and_list_filter(client: TestClient):
    channel = _create_channel(client)
    channel_id = channel["id"]

    bad_create = client.post(
        f"/api/v1/channels/{channel_id}/ideas",
        json=_idea_payload(channel_id, status="not-a-status"),
        headers=_tenant_headers(),
    )
    assert bad_create.status_code == 422

    bad_filter = client.get(f"/api/v1/channels/{channel_id}/ideas", params={"status": "not-a-status"}, headers=_tenant_headers())
    assert bad_filter.status_code == 422
