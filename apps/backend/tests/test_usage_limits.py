from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_starter_cannot_exceed_channel_limit():
    org_id = str(uuid4())
    ch1 = client.post(f"/api/v1/usage/{org_id}/channels/{uuid4()}")
    assert ch1.status_code == 200
    ch2 = client.post(f"/api/v1/usage/{org_id}/channels/{uuid4()}")
    assert ch2.status_code == 409


def test_starter_cannot_exceed_project_limit():
    org_id = str(uuid4())
    payload_base = {
        "organization_id": org_id,
        "workspace_id": str(uuid4()),
        "channel_id": str(uuid4()),
        "title": "Proj",
    }
    for i in range(20):
        res = client.post("/api/v1/video-projects", json={**payload_base, "title": f"p-{i}"})
        assert res.status_code == 201
    blocked = client.post("/api/v1/video-projects", json={**payload_base, "title": "overflow"})
    assert blocked.status_code == 409


def test_pro_has_higher_limits_and_usage_endpoint_works():
    org_id = str(uuid4())
    from app.api.deps import repo_singleton

    repo_singleton.set_plan(UUID(org_id), "pro")
    for _ in range(5):
        assert client.post(f"/api/v1/usage/{org_id}/channels/{uuid4()}").status_code == 200

    usage = client.get(f"/api/v1/usage/{org_id}")
    assert usage.status_code == 200
    body = usage.json()
    assert body["plan"] == "pro"
    assert body["usage"]["channels"] == 5
    assert body["limits"]["max_video_projects_per_month"] == 200
