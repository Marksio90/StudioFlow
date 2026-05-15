import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import get_usage_service, get_video_project_service
from app.db.models import Angle
from app.schemas.topic_research import TopicResearchAnalyzeRequest, TopicResearchReportOut
from app.schemas.video_project import AngleOverridePayload
from app.main import app
from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.ai_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.services.angle_generation_service import AngleGenerationService, AngleGenerationServiceError
from app.services.prompt_registry import build_default_prompt_registry
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
        "name": "Angles Channel",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def _create_idea(client: TestClient, channel_id: str) -> dict:
    payload = {
        "video_project_id": str(uuid4()),
        "channel_id": channel_id,
        "title": "Core idea",
        "description": "Base description",
        "status": "idea",
        "content_pillar": "education",
        "notes": "baseline notes",
    }
    res = client.post(f"/api/v1/channels/{channel_id}/ideas", json=payload, headers=_tenant_headers())
    assert res.status_code == 201, res.text
    return res.json()


def test_angle_model_constraints_declared():
    checks = {constraint.name for constraint in Angle.__table__.constraints if getattr(constraint, "name", None)}
    assert "ck_angles_originality_score_range" in checks
    assert "ck_angles_overall_angle_score_range" in checks


def test_schema_strict_json_and_enum_range_checks():
    with pytest.raises(ValidationError):
        TopicResearchAnalyzeRequest.model_validate({"notes": "ok", "unexpected": True})

    with pytest.raises(ValidationError):
        TopicResearchReportOut.model_validate({
            "recommendation": "invalid",
            "rationale": "because",
            "scores": {
                "demand_score": 1,
                "competition_score": 1,
                "novelty_score": 1,
                "channel_fit_score": 1,
                "execution_risk_score": 1,
                "overall_score": 150,
            },
        })


def test_generate_evaluate_list_approve_override_endpoints(client: TestClient):
    channel = _create_channel(client)
    idea = _create_idea(client, channel["id"])

    generated = client.post(f"/api/v1/ideas/{idea['id']}/angles/generate", json={"count": 2, "prompt": "unexpected hook"}, headers=_tenant_headers())
    assert generated.status_code == 200, generated.text
    angles = generated.json()
    assert len(angles) == 2

    listed = client.get(f"/api/v1/ideas/{idea['id']}/angles", headers=_tenant_headers())
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    evaluated = client.post(
        f"/api/v1/ideas/{idea['id']}/angles/evaluate",
        json={"angle_id": angles[0]["id"]},
        headers=_tenant_headers(),
    )
    assert evaluated.status_code == 200
    assert "overall_score" in evaluated.json()["evaluation"]

    blocked_approval = client.post(
        f"/api/v1/ideas/{idea['id']}/angles/approve",
        json={"angle_id": angles[0]["id"]},
        headers=_tenant_headers(),
    )
    assert blocked_approval.status_code in {200, 409}

    if blocked_approval.status_code == 409:
        overridden = client.post(
            f"/api/v1/ideas/{idea['id']}/angles/override",
            json={"angle_id": angles[0]["id"], "reason": "Human editorial context", "overridden_by": str(uuid4())},
            headers=_tenant_headers(),
        )
        assert overridden.status_code == 200, overridden.text
        assert overridden.json()["override"]["reason"] == "Human editorial context"


def test_gate_rules_each_threshold_and_override_reason_required(client: TestClient):
    channel = _create_channel(client)
    idea = _create_idea(client, channel["id"])

    weak_angle = {
        "headline": "Angle",
        "hook": "x",
        "summary": "guaranteed instant riches",
        "audience": "",
    }
    evaluated = client.post(f"/api/v1/ideas/{idea['id']}/angles/evaluate", json={"angle": weak_angle}, headers=_tenant_headers())
    assert evaluated.status_code == 200

    approve = client.post(f"/api/v1/ideas/{idea['id']}/angles/approve", json={"angle_id": evaluated.json()["id"]}, headers=_tenant_headers())
    assert approve.status_code == 409
    reasons = approve.json().get("details", {}).get("rejection_reasons", [])
    assert any(r["code"] == "HOOK_CLARITY_TOO_LOW" for r in reasons)
    assert any(r["code"] == "RISK_TOO_HIGH" for r in reasons)
    assert any(r["code"] == "OVERALL_SCORE_TOO_LOW" for r in reasons)

    missing_reason = client.post(
        f"/api/v1/ideas/{idea['id']}/angles/override",
        json={"angle_id": evaluated.json()["id"], "reason": "  ", "overridden_by": str(uuid4())},
        headers=_tenant_headers(),
    )
    assert missing_reason.status_code == 422


def test_invalid_score_and_malformed_json_rejections():
    class MalformedProvider(LLMProvider):
        def generate(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(raw_text='{"angles": [}', parsed_json=None, usage=LLMUsage(output_tokens=5))

    class InvalidScoreProvider(LLMProvider):
        def generate(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(raw_text='{"angles": [{"headline":"h","hook":"k","summary":"s","audience":"a"}]}', parsed_json={"angles": []}, usage=LLMUsage(output_tokens=5))

    service = AngleGenerationService(provider=MalformedProvider(), prompt_registry=build_default_prompt_registry())
    with pytest.raises(AngleGenerationServiceError) as malformed:
        service.generate(
            content_idea=type("X", (), {"model_dump": lambda self, mode="json": {"id": str(uuid4()), "channel_id": str(uuid4()), "video_project_id": str(uuid4())}, "video_project_id": uuid4(), "channel_id": uuid4(), "id": uuid4()})(),
            research_brief={},
            channel_memory={},
            count=1,
        )
    assert malformed.value.code == "INVALID_JSON"

    service2 = AngleGenerationService(provider=InvalidScoreProvider(), prompt_registry=build_default_prompt_registry())
    with pytest.raises(AngleGenerationServiceError) as invalid:
        service2.generate(
            content_idea=type("X", (), {"model_dump": lambda self, mode="json": {"id": str(uuid4()), "channel_id": str(uuid4()), "video_project_id": str(uuid4())}, "video_project_id": uuid4(), "channel_id": uuid4(), "id": uuid4()})(),
            research_brief={},
            channel_memory={},
            count=1,
        )
    assert invalid.value.code == "PARTIAL_OUTPUT"


def test_override_payload_requires_reason_min_length():
    with pytest.raises(ValidationError):
        AngleOverridePayload.model_validate({"angle_id": str(uuid4()), "reason": "no", "overridden_by": str(uuid4())})
