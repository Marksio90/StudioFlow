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

    approved = client.post(f'/api/v1/video-projects/{pid}/approve')
    assert approved.status_code == 200
    assert approved.json()['status'] == 'approved'
    project_after_approve = client.get(f'/api/v1/video-projects/{pid}').json()
    assert project_after_approve['status'] == 'approved'

    rejected = client.post(f'/api/v1/video-projects/{pid}/reject')
    assert rejected.status_code == 200
    assert rejected.json()['status'] == 'needs_changes'


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

    approved = client.post(f'/api/v1/video-projects/{pid}/approve')
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
