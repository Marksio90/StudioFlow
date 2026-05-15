from uuid import uuid4

import pytest

from app.schemas.video_project import ContentIdeaOut
from app.services.ai_provider import LLMResponse, LLMUsage
from app.services.topic_research_service import TopicResearchService, TopicResearchServiceError


class _StubProvider:
    def __init__(self, response: LLMResponse):
        self._response = response

    def generate(self, req):
        return self._response


class _StubPromptRegistry:
    def render(self, **kwargs):
        return ("system", "user")


def _content_idea() -> ContentIdeaOut:
    return ContentIdeaOut(
        id=uuid4(),
        video_project_id=uuid4(),
        channel_id=uuid4(),
        title="Idea",
        description="Desc",
        status="idea",
        content_pillar="education",
        target_audience="creators",
        estimated_duration_seconds=600,
        hook="hook",
        angle="angle",
        rationale="rationale",
        score=70,
        notes="notes",
    )


def _valid_report_payload():
    return {
        "recommendation": "approved",
        "rationale": "Solid niche match",
        "summary": "summary",
        "audience_fit": "fit",
        "key_points": ["k1"],
        "demand_signals": ["d1"],
        "competition_notes": ["c1"],
        "content_gaps": ["g1"],
        "suggested_angles": ["a1"],
        "source_queries": ["q1"],
        "confidence": 0.7,
        "scores": {
            "demand_score": 77,
            "competition_score": 40,
            "novelty_score": 74,
            "channel_fit_score": 88,
            "execution_risk_score": 32,
            "overall_score": 76,
        },
    }


def test_topic_research_service_happy_path_with_parsed_json():
    provider = _StubProvider(
        LLMResponse(
            raw_text="{}",
            parsed_json=_valid_report_payload(),
            usage=LLMUsage(input_tokens=10, output_tokens=20, total_tokens=30),
            provider_metadata={"provider": "stub", "model": "stub-model"},
        )
    )
    service = TopicResearchService(provider=provider, prompt_registry=_StubPromptRegistry())

    result = service.analyze(
        content_idea=_content_idea(),
        channel_context={"name": "channel"},
        channel_memory={"notes": []},
        session=None,
    )

    assert result.recommendation.value == "approved"
    assert 0 <= result.scores.overall_score <= 100


def test_topic_research_service_invalid_json_raises_controlled_error():
    provider = _StubProvider(
        LLMResponse(
            raw_text="not-json",
            parsed_json=None,
            usage=LLMUsage(input_tokens=1, output_tokens=1, total_tokens=2),
            provider_metadata={"provider": "stub", "model": "stub-model"},
        )
    )
    service = TopicResearchService(provider=provider, prompt_registry=_StubPromptRegistry())

    with pytest.raises(TopicResearchServiceError) as exc:
        service.analyze(
            content_idea=_content_idea(),
            channel_context={},
            channel_memory={},
            session=None,
        )

    assert exc.value.code == "INVALID_JSON"
    assert "malformed json" in exc.value.message.lower()
