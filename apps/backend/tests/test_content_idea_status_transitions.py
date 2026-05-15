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
    os.environ["AUTH_API_KEYS"] = "editor-key:editor"
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


def _tenant_headers():
    return {
        "X-API-Key": "editor-key",
        "X-Org-Id": "00000000-0000-0000-0000-000000000001",
        "X-Workspace-Id": "00000000-0000-0000-0000-000000000001",
        "X-User-Id": "00000000-0000-0000-0000-000000000011",
    }


def _create_channel(client: TestClient):
    payload = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "name": "Transitions",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_tenant_headers())
    assert res.status_code == 201
    return res.json()


def test_status_transition_endpoint_updates_status_and_rejects_invalid_values(client: TestClient):
    channel = _create_channel(client)
    channel_id = channel["id"]

    create = client.post(
        f"/api/v1/channels/{channel_id}/ideas",
        json={"video_project_id": str(uuid4()), "channel_id": channel_id, "title": "Move me", "status": "idea"},
        headers=_tenant_headers(),
    )
    assert create.status_code == 201
    idea_id = create.json()["id"]

    transition = client.post(f"/api/v1/ideas/{idea_id}/status", json={"status": "approved"}, headers=_tenant_headers())
    assert transition.status_code == 200
    assert transition.json()["status"] == "approved"

    read_back = client.get(f"/api/v1/ideas/{idea_id}", headers=_tenant_headers())
    assert read_back.status_code == 200
    assert read_back.json()["status"] == "approved"

    invalid = client.post(f"/api/v1/ideas/{idea_id}/status", json={"status": "bogus"}, headers=_tenant_headers())
    assert invalid.status_code == 422
