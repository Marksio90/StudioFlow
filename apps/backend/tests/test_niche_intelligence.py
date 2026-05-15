import types
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError

from app.db.models import Channel, LLMCall
from app.schemas.niche_intelligence import NicheAnalysisResult
from app.services.ai_provider import LLMRequest, MockLLMProvider
from app.services.niche_intelligence_service import NicheIntelligenceService


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


def test_niche_analysis_llm_call_populates_channel_without_video_project_id():
    import asyncio

    async def _run():
        channel_id = uuid4()
        channel = Channel(id=channel_id, workspace_id=uuid4(), organization_id=uuid4(), name='Test Channel', youtube_channel_id='yt-test')

        class _Result:
            def __init__(self, *, scalar_one=None, scalars_first=None):
                self._scalar_one = scalar_one
                self._scalars_first = scalars_first

            def scalar_one(self):
                return self._scalar_one

            def scalars(self):
                return types.SimpleNamespace(first=lambda: self._scalars_first)

        session = types.SimpleNamespace(
            execute=AsyncMock(side_effect=[_Result(scalar_one=channel), _Result(scalars_first=None)]),
            add=Mock(),
            commit=AsyncMock(),
            refresh=AsyncMock(),
        )

        prompt_registry = types.SimpleNamespace(render=lambda **kwargs: ('system', 'user prompt'))
        service = NicheIntelligenceService(provider=MockLLMProvider(), prompt_registry=prompt_registry)

        await service.analyze(session, channel_id=channel_id, notes='focus on hooks')

        llm_calls = [call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], LLMCall)]
        assert len(llm_calls) == 1
        assert llm_calls[0].channel_id == channel_id
        assert llm_calls[0].video_project_id is None
        assert llm_calls[0].related_entity_type == 'channel'
        assert llm_calls[0].related_entity_id == channel_id

    asyncio.run(_run())
