from uuid import uuid4
import asyncio

import pytest

from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.ai_provider import LLMProvider, LLMRequest
from app.services.product_agents import LLMProviderError, LLMRequestContext, TrackedLLMClient
from app.services.redaction import redacted_text


class _ExplodingProvider(LLMProvider):
    def generate(self, request: LLMRequest):
        raise RuntimeError("authorization=Bearer super-secret-token api_key=abc123")


def test_redacted_text_masks_known_secret_patterns():
    value = {
        "api_key": "abc123",
        "Authorization": "Bearer top-secret-token",
        "nested": {"token": "123", "safe": "ok"},
        "text": "authorization=Bearer foo token=bar",
    }

    redacted = redacted_text(value)
    assert "abc123" not in redacted
    assert "top-secret-token" not in redacted
    assert "foo" not in redacted
    assert "bar" not in redacted
    assert "[REDACTED]" in redacted


def test_llm_call_logging_redacts_payload_snippets_and_errors():
    repo = InMemoryVideoProjectRepository()
    project_id = uuid4()

    asyncio.run(repo.log_llm_call(
        project_id,
        {
            "provider": "test",
            "model": "test-model",
            "input": {"api_key": "should-hide", "message": "ok"},
            "output": "authorization=Bearer keep-out",
            "error_message": "token=very-secret",
        },
    ))

    row = repo._llm_calls[project_id][0]
    assert "should-hide" not in (row["input_preview"] or "")
    assert "keep-out" not in (row["output_preview"] or "")
    assert "very-secret" not in (row["error_message"] or "")


def test_provider_error_message_is_redacted_before_serialization():
    client = TrackedLLMClient(_ExplodingProvider())
    context = LLMRequestContext(organization_id=uuid4(), workspace_id=uuid4(), video_project_id=uuid4(), workflow_run_id=uuid4())

    with pytest.raises(LLMProviderError) as exc:
        client.generate(task_type="ResearchAgent", payload={"topic": "x"}, context=context)

    underlying = exc.value.__cause__
    assert underlying is not None
    assert "super-secret-token" not in str(underlying)
    assert "abc123" not in str(underlying)
    assert "[REDACTED]" in str(underlying)
