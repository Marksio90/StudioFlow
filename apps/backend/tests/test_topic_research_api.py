import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    os.environ["AUTH_API_KEYS"] = "editor-key:editor"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_API_KEYS", None)


def _headers():
    return {
        "X-API-Key": "editor-key",
        "X-Org-Id": "00000000-0000-0000-0000-000000000001",
        "X-Workspace-Id": "00000000-0000-0000-0000-000000000001",
        "X-User-Id": "00000000-0000-0000-0000-000000000011",
    }


def _create_channel(client: TestClient) -> str:
    payload = {
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "workspace_id": "00000000-0000-0000-0000-000000000001",
        "name": "Research Channel",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_headers())
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _create_idea(client: TestClient, channel_id: str) -> str:
    payload = {
        "video_project_id": str(uuid4()),
        "channel_id": channel_id,
        "title": "Research idea",
        "description": "desc",
        "status": "idea",
        "content_pillar": "education",
    }
    res = client.post(f"/api/v1/channels/{channel_id}/ideas", json=payload, headers=_headers())
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_topic_research_analyze_latest_and_reports_routes(client: TestClient):
    channel_id = _create_channel(client)
    idea_id = _create_idea(client, channel_id)

    first = client.post(f"/api/v1/ideas/{idea_id}/research/analyze", headers=_headers())
    second = client.post(f"/api/v1/ideas/{idea_id}/research/analyze", headers=_headers())
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    latest = client.get(f"/api/v1/ideas/{idea_id}/research/latest", headers=_headers())
    assert latest.status_code == 200, latest.text
    assert latest.json()["id"] == second.json()["id"]

    reports = client.get(f"/api/v1/ideas/{idea_id}/research/reports", headers=_headers())
    assert reports.status_code == 200, reports.text
    items = reports.json()["items"]
    assert len(items) >= 2
    assert items[0]["id"] == second.json()["id"]
    assert items[1]["id"] == first.json()["id"]
