import pytest

from app.schemas.topic_research import TopicResearchRecommendation


@pytest.mark.parametrize(
    "value",
    ["approved", "needs_more_research", "too_generic", "reject"],
)
def test_topic_research_recommendation_allows_only_expected_values(value: str):
    assert TopicResearchRecommendation(value).value == value


@pytest.mark.parametrize("value", ["pursue", "refine", "hold", ""])
def test_topic_research_recommendation_rejects_unknown_values(value: str):
    with pytest.raises(ValueError):
        TopicResearchRecommendation(value)
