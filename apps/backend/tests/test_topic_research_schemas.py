import pytest
from pydantic import ValidationError

from app.schemas.topic_research import TopicResearchReportOut


def _valid_payload(**overrides):
    payload = {
        "recommendation": "approved",
        "rationale": "Strong fit and demand.",
        "summary": "A concise summary",
        "audience_fit": "Great for returning viewers",
        "key_points": ["Point 1"],
        "demand_signals": ["signal"],
        "competition_notes": ["note"],
        "content_gaps": ["gap"],
        "suggested_angles": ["angle"],
        "source_queries": ["query"],
        "confidence": 0.8,
        "scores": {
            "demand_score": 80,
            "competition_score": 45,
            "novelty_score": 70,
            "channel_fit_score": 90,
            "execution_risk_score": 30,
            "overall_score": 78,
        },
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("field", [
    "demand_score",
    "competition_score",
    "novelty_score",
    "channel_fit_score",
    "execution_risk_score",
    "overall_score",
])
def test_topic_research_scores_enforce_bounds(field: str):
    low = _valid_payload()
    low["scores"][field] = -1
    with pytest.raises(ValidationError):
        TopicResearchReportOut.model_validate(low)

    high = _valid_payload()
    high["scores"][field] = 101
    with pytest.raises(ValidationError):
        TopicResearchReportOut.model_validate(high)


def test_topic_research_recommendation_enum_validation():
    payload = _valid_payload(recommendation="pursue")
    with pytest.raises(ValidationError):
        TopicResearchReportOut.model_validate(payload)


def test_topic_research_schema_rejects_extra_fields_strict_mode():
    payload = _valid_payload(unexpected_field="nope")
    with pytest.raises(ValidationError):
        TopicResearchReportOut.model_validate(payload)
