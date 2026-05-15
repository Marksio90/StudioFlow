from uuid import uuid4
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_usage_service, get_video_project_service
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


def _tenant_headers(role_key: str = "editor-key", org_id: str | None = None, workspace_id: str | None = None):
    return {"X-API-Key": role_key, "X-Org-Id": org_id or "00000000-0000-0000-0000-000000000001", "X-Workspace-Id": workspace_id or "00000000-0000-0000-0000-000000000001", "X-User-Id": "00000000-0000-0000-0000-000000000011"}


def _create_channel(client: TestClient):
    payload = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "name": "Primary",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def test_channels_crud_lifecycle(client: TestClient):
    created = _create_channel(client)
    channel_id = created["id"]

    fetched = client.get(f"/api/v1/channels/{channel_id}", headers=_tenant_headers())
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Primary"

    listing = client.get("/api/v1/channels", headers=_tenant_headers())
    assert listing.status_code == 200
    assert any(item["id"] == channel_id for item in listing.json()["items"])

    patched = client.patch(f"/api/v1/channels/{channel_id}", json={"name": "Renamed"}, headers=_tenant_headers())
    assert patched.status_code == 200
    assert patched.json()["name"] == "Renamed"

    deleted = client.delete(f"/api/v1/channels/{channel_id}", headers=_tenant_headers())
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/channels/{channel_id}", headers=_tenant_headers())
    assert missing.status_code == 404


def test_channel_memory_read_update_lifecycle(client: TestClient):
    created = _create_channel(client)
    channel_id = created["id"]

    initial = client.get(f"/api/v1/channels/{channel_id}/memory", headers=_tenant_headers())
    assert initial.status_code == 200
    assert initial.json()["memory"]["banned_phrases"] == []

    payload = {
        "approved_title_patterns": ["A vs B"],
        "rejected_title_patterns": [],
        "thumbnail_rules": {"face": True},
        "banned_phrases": ["No clickbait", "NO CLICKBAIT"],
        "preferred_phrases": ["evidence-based"],
        "compliance_preferences": {"disclosures": True},
        "narrator_style": {"tone": "calm"},
        "visual_style": {"palette": "warm"},
        "audience_objections": ["too complex"],
        "best_performing_patterns": ["myth busting"],
        "worst_performing_patterns": ["listicle"],
        "freeform_memory_notes": ["Keep first 15s snappy"],
    }
    updated = client.patch(f"/api/v1/channels/{channel_id}/memory", json=payload, headers=_tenant_headers())
    assert updated.status_code == 200
    assert updated.json()["memory"]["banned_phrases"] == ["No clickbait"]

    reloaded = client.get(f"/api/v1/channels/{channel_id}/memory", headers=_tenant_headers())
    assert reloaded.status_code == 200
    assert reloaded.json()["memory"]["thumbnail_rules"] == {"face": True}


def test_channel_tenant_and_auth_boundaries(client: TestClient):
    created = _create_channel(client)
    channel_id = created["id"]

    unauth = client.get(f"/api/v1/channels/{channel_id}")
    assert unauth.status_code == 401

    viewer_cannot_mutate = client.patch(f"/api/v1/channels/{channel_id}", json={"name": "Nope"}, headers=_tenant_headers(role_key="viewer-key"))
    assert viewer_cannot_mutate.status_code == 403

    cross_tenant = client.get(f"/api/v1/channels/{channel_id}", headers=_tenant_headers(org_id=str(uuid4()), workspace_id=str(uuid4())))
    assert cross_tenant.status_code == 403
