from pydantic import ValidationError

from app.schemas.niche_intelligence import NicheAnalysisResult
from app.services.ai_provider import LLMRequest, MockLLMProvider


def test_niche_schema_validates_score_ranges():
    valid = MockLLMProvider().generate(LLMRequest(task_type='NicheIntelligenceAgent')).parsed_json
    result = NicheAnalysisResult.model_validate(valid)
    assert 0 <= result.scores.overall_score <= 100


def test_niche_schema_rejects_out_of_range_score():
    payload = MockLLMProvider().generate(LLMRequest(task_type='NicheIntelligenceAgent')).parsed_json
    payload['scores']['overall_score'] = 120
    try:
        NicheAnalysisResult.model_validate(payload)
        assert False
    except ValidationError:
        assert True


def test_niche_schema_rejects_invalid_json_shape():
    try:
        NicheAnalysisResult.model_validate({'summary': 'x'})
        assert False
    except ValidationError:
        assert True
