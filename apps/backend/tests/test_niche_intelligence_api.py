from datetime import datetime, timezone
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_llm_provider
from app.main import app
from app.services.ai_provider import MockLLMProvider
from app.services.niche_intelligence_service import NicheIntelligenceService


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


def test_niche_analyze_uses_provider_dependency_override(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    channel_id = _create_channel(client)

    chosen_provider = MockLLMProvider()

    def override_provider():
        return chosen_provider

    observed = {}

    async def fake_analyze(self, session, *, channel_id, notes):
        observed["provider"] = self.provider
        return SimpleNamespace(
            id=uuid4(),
            channel_id=channel_id,
            summary="stub summary",
            score_explanations={"overall_score": "stub"},
            strengths=["strength"],
            weaknesses=["weakness"],
            risks=["risk"],
            recommended_positioning="positioning",
            content_pillar_suggestions=["pillar"],
            differentiation_opportunities=["diff"],
            compliance_notes=["note"],
            next_actions=["next"],
            scores={
                "demand_score": 70,
                "competition_score": 60,
                "originality_potential": 80,
                "production_difficulty": 50,
                "monetization_potential": 65,
                "compliance_risk": 30,
                "long_term_depth": 75,
                "overall_score": 72,
            },
            created_at=datetime.now(timezone.utc),
        )

    app.dependency_overrides[get_llm_provider] = override_provider
    monkeypatch.setattr(NicheIntelligenceService, "analyze", fake_analyze)

    res = client.post(f"/api/v1/channels/{channel_id}/niche/analyze", json={"notes": "test notes"}, headers=_headers())

    assert res.status_code == 200, res.text
    assert observed["provider"] is chosen_provider
