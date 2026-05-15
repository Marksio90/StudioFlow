import json
import hashlib
from uuid import UUID

from sqlalchemy import select

from app.db.models import Channel, ChannelMemory, LLMCall, NicheIntelligenceReport
from app.schemas.niche_intelligence import NicheAnalysisResult
from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest
from app.services.prompt_registry import PromptRegistry, serialize_untrusted_block


class NicheIntelligenceService:
    def __init__(self, provider: LLMProvider, prompt_registry: PromptRegistry):
        self.provider = provider
        self.prompt_registry = prompt_registry

    async def analyze(self, session, *, channel_id: UUID, notes: str) -> NicheIntelligenceReport:
        channel = (await session.execute(select(Channel).where(Channel.id == channel_id))).scalar_one()
        memory = (await session.execute(select(ChannelMemory).where(ChannelMemory.channel_id == channel_id).order_by(ChannelMemory.created_at.desc()))).scalars().first()
        payload = {
            'channel': {
                'id': str(channel.id),
                'name': channel.name,
                'description': channel.description,
                'niche': channel.niche,
                'language': channel.language,
                'target_audience': channel.target_audience,
                'tone_of_voice': channel.tone_of_voice,
                'content_pillars': channel.content_pillars,
                'brand_rules': channel.brand_rules,
            },
            'channel_memory': memory.memory if memory else {},
            'user_notes': notes,
        }
        system_prompt, user_prompt = self.prompt_registry.render(name='niche_intelligence_analyze', version='v1', variables={'payload_json': serialize_untrusted_block(payload)})
        req = LLMRequest(task_type='NicheIntelligenceAgent', system_prompt=system_prompt, messages=[LLMMessage(role='user', content=user_prompt, trusted=False)])
        response = self.provider.generate(req)
        parsed = response.parsed_json
        if parsed is None:
            parsed = json.loads(response.raw_text)
        result = NicheAnalysisResult.model_validate(parsed)
        report = NicheIntelligenceReport(channel_id=channel_id, **result.model_dump())
        session.add(report)
        llm_call = LLMCall(video_project_id=None, channel_id=channel_id, provider=str(response.provider_metadata.get('provider', 'unknown')), model=str(response.provider_metadata.get('model', 'unknown')), prompt_template_name='niche_intelligence_analyze', prompt_template_version='v1', input_hash=hashlib.sha256(user_prompt.encode()).hexdigest(), input_preview=user_prompt[:500], output_hash=hashlib.sha256(response.raw_text.encode()).hexdigest(), output_preview=response.raw_text[:500], prompt_tokens=response.usage.input_tokens, completion_tokens=response.usage.output_tokens, total_tokens=response.usage.total_tokens or (response.usage.input_tokens + response.usage.output_tokens), related_entity_type='channel', related_entity_id=channel_id)
        session.add(llm_call)
        await session.commit()
        await session.refresh(report)
        return report
