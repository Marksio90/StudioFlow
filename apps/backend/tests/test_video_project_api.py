from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_payload():
    return {
        "organization_id": str(uuid4()),
        "workspace_id": str(uuid4()),
        "channel_id": str(uuid4()),
        "title": "My Project",
    }


def test_crud_and_workflow_endpoints():
    created = client.post('/api/v1/video-projects', json=create_payload())
    assert created.status_code == 201
    pid = created.json()['id']

    assert client.get('/api/v1/video-projects').status_code == 200
    assert client.get(f'/api/v1/video-projects/{pid}').status_code == 200
    assert client.patch(f'/api/v1/video-projects/{pid}', json={"status": "researching"}).status_code == 200

    assert client.post(f'/api/v1/video-projects/{pid}/start-workflow').status_code == 200
    assert client.post(f'/api/v1/video-projects/{pid}/request-approval').status_code == 200
    assert client.post(f'/api/v1/video-projects/{pid}/approve').status_code == 200
    assert client.post(f'/api/v1/video-projects/{pid}/reject').status_code == 200

    events = client.get(f'/api/v1/video-projects/{pid}/events')
    assert events.status_code == 200
    assert any(e['event_type'] == 'workflow.created' for e in events.json())

    assert client.get(f'/api/v1/video-projects/{pid}/costs').status_code == 200
    assert client.get(f'/api/v1/video-projects/{pid}/quota').status_code == 200
    assert client.get(f'/api/v1/video-projects/{pid}/compliance').status_code == 200
    assert client.get(f'/api/v1/video-projects/{pid}/analytics').status_code == 200

    assert client.delete(f'/api/v1/video-projects/{pid}').status_code == 204


def test_filters_and_error_structure_and_openapi():
    payload = create_payload()
    client.post('/api/v1/video-projects', json=payload)
    r = client.get(f"/api/v1/video-projects?status=draft&channel_id={payload['channel_id']}&workspace_id={payload['workspace_id']}")
    assert r.status_code == 200
    assert 'items' in r.json()

    missing = client.get(f'/api/v1/video-projects/{uuid4()}', headers={"x-correlation-id": "cid-1"})
    assert missing.status_code == 404
    assert missing.json()['detail']['error']['correlation_id'] == 'cid-1'

    assert client.get('/openapi.json').status_code == 200
