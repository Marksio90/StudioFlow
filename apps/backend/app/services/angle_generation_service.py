from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.video_project import ContentIdeaOut
from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest
from app.services.prompt_registry import PromptRegistry, serialize_untrusted_block


class GeneratedAngle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    headline: str = Field(min_length=1)
    hook: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    audience: str = Field(min_length=1)


class AngleGenerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    angles: list[GeneratedAngle] = Field(min_length=1)


class AngleGenerationServiceError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class AngleGenerationService:
    TASK_TYPE = "angle_generation"
    PROMPT_NAME = "angle_generate"
    PROMPT_VERSION = "v1"

    def __init__(self, *, provider: LLMProvider, prompt_registry: PromptRegistry) -> None:
        self.provider = provider
        self.prompt_registry = prompt_registry

    def generate(
        self,
        *,
        content_idea: ContentIdeaOut,
        research_brief: dict[str, Any],
        channel_memory: dict[str, Any],
        count: int,
    ) -> AngleGenerationOutput:
        payload = {
            "count": count,
            "content_idea": content_idea.model_dump(mode="json"),
            "research_brief": research_brief,
            "channel_memory": channel_memory,
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

        raw_payload = response.parsed_json
        if raw_payload is None:
            try:
                raw_payload = json.loads(response.raw_text)
            except json.JSONDecodeError as exc:
                raise AngleGenerationServiceError(
                    code="INVALID_JSON",
                    message="Provider returned malformed JSON",
                    details={"error": str(exc), "raw_text_preview": response.raw_text[:500]},
                ) from exc

        try:
            parsed = AngleGenerationOutput.model_validate(raw_payload)
        except ValidationError as exc:
            raise AngleGenerationServiceError(
                code="INVALID_SCHEMA",
                message="Provider JSON did not match angle generation schema",
                details={"errors": exc.errors()},
            ) from exc

        if len(parsed.angles) != count:
            raise AngleGenerationServiceError(
                code="PARTIAL_OUTPUT",
                message="Provider returned a different number of angles than requested",
                details={"expected_count": count, "actual_count": len(parsed.angles)},
            )

        return parsed
