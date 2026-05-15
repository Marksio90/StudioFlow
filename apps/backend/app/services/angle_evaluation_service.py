from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.db.models import LLMCall
from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest
from app.services.prompt_registry import PromptRegistry, serialize_untrusted_block


class AngleRecommendation(str, Enum):
    approve = "approve"
    refine = "refine"
    reject = "reject"


class AngleScorecard(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    hook_clarity: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    audience_fit: float = Field(ge=0, le=1)
    risk: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)


class EvaluatedAngle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    angle_index: int = Field(ge=0)
    scores: AngleScorecard
    recommendation: AngleRecommendation
    rationale: str = Field(min_length=1)


class AngleEvaluationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    evaluations: list[EvaluatedAngle] = Field(min_length=1)


class AngleEvaluationServiceError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class AngleEvaluationService:
    TASK_TYPE = "angle_evaluation"
    PROMPT_NAME = "angle_evaluate"
    PROMPT_VERSION = "v1"

    def __init__(self, *, provider: LLMProvider, prompt_registry: PromptRegistry) -> None:
        self.provider = provider
        self.prompt_registry = prompt_registry

    def evaluate(
        self,
        *,
        candidates: list[dict[str, Any]],
        content_idea: dict[str, Any],
        research_brief: dict[str, Any],
        channel_memory: dict[str, Any],
        session: Any | None = None,
    ) -> AngleEvaluationOutput:
        payload = {
            "content_idea": content_idea,
            "research_brief": research_brief,
            "channel_memory": channel_memory,
            "candidates": candidates,
        }
        system_prompt, user_prompt = self.prompt_registry.render(
            name=self.PROMPT_NAME,
            version=self.PROMPT_VERSION,
            variables={"payload_json": serialize_untrusted_block(payload)},
        )

        request = LLMRequest(
            task_type=self.TASK_TYPE,
            system_prompt=system_prompt,
            messages=[LLMMessage(role="user", content=user_prompt, trusted=False)],
        )
        response = self.provider.generate(request)
        if session is not None:
            first_angle_id = next((candidate.get("id") for candidate in candidates if isinstance(candidate, dict) and candidate.get("id")), None)
            session.add(
                LLMCall(
                    video_project_id=content_idea.get("video_project_id"),
                    channel_id=content_idea.get("channel_id"),
                    provider=str(response.provider_metadata.get("provider", "unknown")),
                    model=str(response.provider_metadata.get("model", "unknown")),
                    prompt_template_name=self.PROMPT_NAME,
                    prompt_template_version=self.PROMPT_VERSION,
                    input_hash=hashlib.sha256(user_prompt.encode()).hexdigest(),
                    input_preview=user_prompt[:500],
                    output_hash=hashlib.sha256(response.raw_text.encode()).hexdigest(),
                    output_preview=response.raw_text[:500],
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.total_tokens or (response.usage.input_tokens + response.usage.output_tokens),
                    estimated_cost_usd=response.provider_metadata.get("estimated_cost_usd"),
                    related_entity_type="Angle",
                    related_entity_id=first_angle_id,
                )
            )

        raw_payload = response.parsed_json
        if raw_payload is None:
            try:
                raw_payload = json.loads(response.raw_text)
            except json.JSONDecodeError as exc:
                raise AngleEvaluationServiceError(
                    code="INVALID_JSON",
                    message="Provider returned malformed JSON",
                    details={"error": str(exc), "raw_text_preview": response.raw_text[:500]},
                ) from exc

        try:
            parsed = AngleEvaluationOutput.model_validate(raw_payload)
        except ValidationError as exc:
            raise AngleEvaluationServiceError(
                code="INVALID_SCHEMA",
                message="Provider JSON did not match angle evaluation schema",
                details={"errors": exc.errors()},
            ) from exc

        expected_indexes = set(range(len(candidates)))
        returned_indexes = {item.angle_index for item in parsed.evaluations}
        if returned_indexes != expected_indexes:
            raise AngleEvaluationServiceError(
                code="PARTIAL_OUTPUT",
                message="Provider did not return exactly one evaluation per candidate",
                details={
                    "expected_indexes": sorted(expected_indexes),
                    "returned_indexes": sorted(returned_indexes),
                },
            )

        return parsed
