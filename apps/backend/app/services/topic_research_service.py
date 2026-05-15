from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.schemas.video_project import ContentIdeaOut
from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest
from app.services.model_router import ModelRouter
from app.services.prompt_registry import PromptRegistry, serialize_untrusted_block


class TopicRecommendation(str, Enum):
    pursue = "pursue"
    refine = "refine"
    reject = "reject"


class TopicResearchServiceError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class TopicResearchScores(BaseModel):
    demand_score: int = Field(ge=0, le=100)
    competition_score: int = Field(ge=0, le=100)
    novelty_score: int = Field(ge=0, le=100)
    channel_fit_score: int = Field(ge=0, le=100)
    execution_risk_score: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)

    @field_validator("*")
    @classmethod
    def _to_clamped_int(cls, value: int | float) -> int:
        if not isinstance(value, (int, float)):
            raise TypeError("score must be numeric")
        return max(0, min(100, int(round(value))))


class TopicResearchOutput(BaseModel):
    recommendation: TopicRecommendation
    rationale: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    scores: TopicResearchScores


class TopicResearchService:
    TASK_TYPE = "research"
    PROMPT_NAME = "topic_research_analyze"
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        *,
        provider: LLMProvider,
        prompt_registry: PromptRegistry,
        model_router: ModelRouter | None = None,
    ) -> None:
        self.provider = provider
        self.prompt_registry = prompt_registry
        self.model_router = model_router or ModelRouter()

    def analyze(
        self,
        *,
        content_idea: ContentIdeaOut,
        channel_context: dict[str, Any],
        channel_memory: dict[str, Any],
    ) -> TopicResearchOutput:
        payload = {
            "content_idea": content_idea.model_dump(mode="json"),
            "channel_context": channel_context,
            "channel_memory": channel_memory,
        }

        system_prompt, user_prompt = self.prompt_registry.render(
            name=self.PROMPT_NAME,
            version=self.PROMPT_VERSION,
            variables={"payload_json": serialize_untrusted_block(payload)},
        )

        llm_config = self.model_router.resolve(task_type=self.TASK_TYPE)
        request = LLMRequest(
            task_type=self.TASK_TYPE,
            provider_metadata={"provider": llm_config.provider, "model": llm_config.model},
            system_prompt=system_prompt,
            messages=[LLMMessage(role="user", content=user_prompt, trusted=False)],
        )

        response = self.provider.generate(request)
        raw_payload = response.parsed_json
        if raw_payload is None:
            try:
                raw_payload = json.loads(response.raw_text)
            except json.JSONDecodeError as exc:
                raise TopicResearchServiceError(
                    code="INVALID_JSON",
                    message="Provider returned malformed JSON",
                    details={"error": str(exc), "raw_text_preview": response.raw_text[:500]},
                ) from exc

        try:
            return TopicResearchOutput.model_validate(raw_payload)
        except ValidationError as exc:
            raise TopicResearchServiceError(
                code="INVALID_SCHEMA",
                message="Provider JSON did not match topic research schema",
                details={"errors": exc.errors()},
            ) from exc
