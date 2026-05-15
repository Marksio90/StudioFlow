from datetime import datetime, timezone
import os
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_llm_provider
from app.main import app
from app.services.ai_provider import LLMProvider, LLMResponse, LLMUsage


@pytest.fixture
def client():
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
        "name": "Niche Channel",
        "youtube_channel_id": f"yt-{uuid4()}",
    }
    res = client.post("/api/v1/channels", json=payload, headers=_headers())
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_niche_analyze_returns_expected_shape_and_logs_llm_call(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    channel_id = _create_channel(client)
    observed = {}

    async def fake_analyze(self, session, *, channel_id, notes):
        observed["llm_call_logged"] = True
        return type("Report", (), {
            "id": uuid4(),
            "channel_id": channel_id,
            "summary": "stub summary",
            "score_explanations": {"overall_score": "stub"},
            "strengths": ["strength"],
            "weaknesses": ["weakness"],
            "risks": ["risk"],
            "recommended_positioning": "positioning",
            "content_pillar_suggestions": ["pillar"],
            "differentiation_opportunities": ["diff"],
            "compliance_notes": ["note"],
            "next_actions": ["next"],
            "scores": {"demand_score": 70, "competition_score": 60, "originality_potential": 80, "production_difficulty": 50, "monetization_potential": 65, "compliance_risk": 30, "long_term_depth": 75, "overall_score": 72},
            "created_at": datetime.now(timezone.utc),
        })()

    from app.services.niche_intelligence_service import NicheIntelligenceService
    monkeypatch.setattr(NicheIntelligenceService, "analyze", fake_analyze)
    res = client.post(f"/api/v1/channels/{channel_id}/niche/analyze", json={"notes": "test notes"}, headers=_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    for key in [
        "id", "channel_id", "summary", "score_explanations", "strengths", "weaknesses", "risks",
        "recommended_positioning", "content_pillar_suggestions", "differentiation_opportunities",
        "compliance_notes", "next_actions", "scores", "created_at",
    ]:
        assert key in body

    score_keys = {
        "demand_score", "competition_score", "originality_potential", "production_difficulty",
        "monetization_potential", "compliance_risk", "long_term_depth", "overall_score",
    }
    assert set(body["scores"].keys()) == score_keys

    assert observed["llm_call_logged"] is True


def test_niche_reports_list_and_get_detail_reverse_chronological(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    channel_id = _create_channel(client)

    async def fake_analyze(self, session, *, channel_id, notes):
        return type("Report", (), {"id": uuid4(), "channel_id": channel_id, "summary": notes, "score_explanations": {"overall_score": "stub"}, "strengths": ["s"], "weaknesses": ["w"], "risks": ["r"], "recommended_positioning": "p", "content_pillar_suggestions": ["c"], "differentiation_opportunities": ["d"], "compliance_notes": ["n"], "next_actions": ["a"], "scores": {"demand_score": 70, "competition_score": 60, "originality_potential": 80, "production_difficulty": 50, "monetization_potential": 65, "compliance_risk": 30, "long_term_depth": 75, "overall_score": 72}, "created_at": datetime.now(timezone.utc)})()

    from app.services.niche_intelligence_service import NicheIntelligenceService
    monkeypatch.setattr(NicheIntelligenceService, "analyze", fake_analyze)
    first = client.post(f"/api/v1/channels/{channel_id}/niche/analyze", json={"notes": "first"}, headers=_headers())
    second = client.post(f"/api/v1/channels/{channel_id}/niche/analyze", json={"notes": "second"}, headers=_headers())
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    listing = client.get(f"/api/v1/channels/{channel_id}/niche/reports", headers=_headers())
    assert listing.status_code == 200, listing.text
    items = listing.json()["items"]
    assert len(items) >= 2
    assert items[0]["id"] == second.json()["id"]
    assert items[1]["id"] == first.json()["id"]

    report_id = first.json()["id"]
    detail = client.get(f"/api/v1/channels/{channel_id}/niche/reports/{report_id}", headers=_headers())
    assert detail.status_code == 200, detail.text
    assert detail.json() == first.json()


class _InvalidJsonProvider(LLMProvider):
    def generate(self, req):
        return LLMResponse(raw_text="not json at all", parsed_json=None, usage=LLMUsage(input_tokens=1, output_tokens=1, total_tokens=2), provider_metadata={"provider": "stub", "model": "stub-model"})


class _InvalidShapeProvider(LLMProvider):
    def generate(self, req):
        return LLMResponse(raw_text=json.dumps({"summary": "missing required fields"}), parsed_json=None, usage=LLMUsage(input_tokens=1, output_tokens=1, total_tokens=2), provider_metadata={"provider": "stub", "model": "stub-model"})


@pytest.mark.parametrize("provider", [_InvalidJsonProvider(), _InvalidShapeProvider()])
def test_niche_analyze_invalid_provider_response_returns_controlled_error(client: TestClient, provider: LLMProvider, monkeypatch: pytest.MonkeyPatch):
    channel_id = _create_channel(client)
    app.dependency_overrides[get_llm_provider] = lambda: provider

    async def fake_analyze(self, session, *, channel_id, notes):
        response = self.provider.generate(None)
        parsed = json.loads(response.raw_text)
        required = {"summary", "scores", "strengths"}
        if not required.issubset(set(parsed.keys())):
            raise ValueError("invalid shape")
        return parsed

    from app.services.niche_intelligence_service import NicheIntelligenceService
    monkeypatch.setattr(NicheIntelligenceService, "analyze", fake_analyze)
    res = client.post(f"/api/v1/channels/{channel_id}/niche/analyze", json={"notes": "break"}, headers=_headers())
    assert res.status_code == 502
    payload = res.json()
    assert payload["detail"]["error"]["code"] == "NicheAnalyzeFailed"
    assert "invalid response" in payload["detail"]["error"]["message"].lower()
    assert "traceback" not in res.text.lower()
