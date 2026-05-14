from uuid import UUID
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import repo_singleton
from app.main import app

client = TestClient(app)


def create_payload():
    return {
        "organization_id": str(uuid4()),
        "workspace_id": str(uuid4()),
        "channel_id": str(uuid4()),
        "title": "My Project",
    }


def test_workflow_e2e_scenario():
    created = client.post('/api/v1/video-projects', json=create_payload())
    assert created.status_code == 201
    pid = created.json()['id']

    started = client.post(f'/api/v1/video-projects/{pid}/start-workflow')
    assert started.status_code == 200

    project = client.get(f'/api/v1/video-projects/{pid}').json()
    assert project['status'] == 'awaiting_review'

    steps = repo_singleton.workflow_steps[UUID(pid)]
    assert any(s['step_name'] == 'wait_for_approval' and s['status'] == 'waiting_for_approval' for s in steps)

    events = client.get(f'/api/v1/video-projects/{pid}/events').json()
    event_types = [e['event_type'] for e in events]
    assert 'workflow.created' in event_types
    assert 'workflow.waiting_for_approval' in event_types

    approved = client.post(f'/api/v1/video-projects/{pid}/approve', json={'comment':'ok','decided_by_user_id': str(uuid4())})
    assert approved.status_code == 200
    assert approved.json()['status'] == 'approved'
    project_after_approve = client.get(f'/api/v1/video-projects/{pid}').json()
    assert project_after_approve['status'] == 'approved'

    rejected = client.post(f'/api/v1/video-projects/{pid}/reject', json={'comment':'no','decided_by_user_id': str(uuid4())})
    assert rejected.status_code == 200
    assert rejected.json()['status'] == 'rejected'


def test_compliance_can_block_approval():
    created = client.post('/api/v1/video-projects', json=create_payload())
    pid = created.json()['id']
    client.post(f'/api/v1/video-projects/{pid}/start-workflow')

    compliance = client.post(
        f'/api/v1/video-projects/{pid}/compliance',
        json={
            "metadata": {
                "score": 91,
                "requires_ai_disclosure": True,
                "copyright_risk": "high",
            },
            "disclosure_decision_missing": True,
        },
    )
    assert compliance.status_code == 200
    assert compliance.json()['risk_level'] == 'blocked'

    approved = client.post(f'/api/v1/video-projects/{pid}/approve', json={'comment':'ok','decided_by_user_id': str(uuid4())})
    assert approved.status_code == 200
    assert approved.json()['status'] == 'blocked'


def test_crud_filters_and_openapi():
    payload = create_payload()
    created = client.post('/api/v1/video-projects', json=payload)
    pid = created.json()['id']

    assert client.get('/api/v1/video-projects').status_code == 200
    assert client.patch(f'/api/v1/video-projects/{pid}', json={"status": "researching"}).status_code == 200
    assert client.get(f"/api/v1/video-projects?status=researching&channel_id={payload['channel_id']}&workspace_id={payload['workspace_id']}").status_code == 200

    missing = client.get(f'/api/v1/video-projects/{uuid4()}', headers={"x-correlation-id": "cid-1"})
    assert missing.status_code == 404
    assert missing.json()['detail']['error']['correlation_id'] == 'cid-1'

    assert client.get('/openapi.json').status_code == 200
    assert client.delete(f'/api/v1/video-projects/{pid}').status_code == 204


def test_costs_endpoint_returns_aggregated_llm_costs():
    created = client.post('/api/v1/video-projects', json=create_payload())
    pid = created.json()['id']
    project_uuid = UUID(pid)

    repo_singleton.log_llm_cost_entry(project_uuid, {"cost_usd": 0.001})
    repo_singleton.log_llm_cost_entry(project_uuid, {"cost_usd": 0.0025})

    costs = client.get(f'/api/v1/video-projects/{pid}/costs')
    assert costs.status_code == 200
    assert costs.json()['total_cost_usd'] == 0.0035


def test_quota_endpoint_returns_project_and_channel_aggregation():
    payload = create_payload()
    created = client.post('/api/v1/video-projects', json=payload)
    pid = created.json()['id']
    project_uuid = UUID(pid)

    # second project in the same channel to validate channel aggregation
    created2 = client.post('/api/v1/video-projects', json={**payload, "title": "Second"})
    project2_uuid = UUID(created2.json()['id'])

    repo_singleton.log_youtube_quota_entry({
        "organization_id": UUID(payload["organization_id"]),
        "workspace_id": UUID(payload["workspace_id"]),
        "channel_id": UUID(payload["channel_id"]),
        "video_project_id": project_uuid,
        "workflow_run_id": uuid4(),
        "youtube_method": "videos.list",
        "quota_cost": 1,
        "success": True,
        "retry_of_id": None,
    })
    repo_singleton.log_youtube_quota_entry({
        "organization_id": UUID(payload["organization_id"]),
        "workspace_id": UUID(payload["workspace_id"]),
        "channel_id": UUID(payload["channel_id"]),
        "video_project_id": project_uuid,
        "workflow_run_id": uuid4(),
        "youtube_method": "videos.insert",
        "quota_cost": 1600,
        "success": False,
        "retry_of_id": uuid4(),
    })
    repo_singleton.log_youtube_quota_entry({
        "organization_id": UUID(payload["organization_id"]),
        "workspace_id": UUID(payload["workspace_id"]),
        "channel_id": UUID(payload["channel_id"]),
        "video_project_id": project2_uuid,
        "workflow_run_id": uuid4(),
        "youtube_method": "search.list",
        "quota_cost": 100,
        "success": True,
        "retry_of_id": None,
    })

    quota = client.get(f'/api/v1/video-projects/{pid}/quota')
    assert quota.status_code == 200
    body = quota.json()
    assert body['project_quota_cost'] == 1601
    assert body['channel_quota_cost'] == 1701


def test_needs_changes_and_decision_history_available():
    created = client.post('/api/v1/video-projects', json=create_payload())
    pid = created.json()['id']
    client.post(f'/api/v1/video-projects/{pid}/request-approval')

    change = client.post(
        f'/api/v1/video-projects/{pid}/needs-changes',
        json={'comment': 'update intro', 'decided_by_user_id': str(uuid4())},
    )
    assert change.status_code == 200
    assert change.json()['status'] == 'needs_changes'

    project = client.get(f'/api/v1/video-projects/{pid}').json()
    assert project['status'] == 'needs_changes'

    history = client.get(f'/api/v1/video-projects/{pid}/approval-decisions')
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]['comment'] == 'update intro'

def test_analytics_snapshot_create_and_list():
    payload = create_payload()
    created = client.post('/api/v1/video-projects', json=payload)
    pid = created.json()['id']

    snap_payload = {
        "channel_id": payload["channel_id"],
        "youtube_video_id": "yt_123",
        "views": 1234,
        "watch_time_minutes": 456.7,
        "average_view_duration": 89.1,
        "ctr": 4.2,
        "likes": 111,
        "comments": 22,
        "subscribers_gained": 9,
        "estimated_revenue": 12.34,
        "snapshot_at": "2026-05-14T10:00:00Z",
    }
    saved = client.post(f'/api/v1/video-projects/{pid}/analytics', json=snap_payload)
    assert saved.status_code == 201
    assert saved.json()['youtube_video_id'] == 'yt_123'

    rows = client.get(f'/api/v1/video-projects/{pid}/analytics')
    assert rows.status_code == 200
    assert len(rows.json()) == 1
    assert rows.json()[0]['views'] == 1234
