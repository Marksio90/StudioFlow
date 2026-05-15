from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    task_type: str
    messages: list[LLMMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    user_content: str | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class LLMUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    raw_text: str
    parsed_json: dict[str, Any] | None = None
    messages: list[LLMMessage] = Field(default_factory=list)
    usage: LLMUsage = Field(default_factory=LLMUsage)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse: ...


@dataclass
class OpenAICompatibleProvider:
    base_url: str
    api_key: str
    model: str
    timeout: float = 30.0

    def generate(self, request: LLMRequest) -> LLMResponse:
        import json
        from urllib import request as urlrequest

        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._build_messages(request),
        }
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(endpoint, data=body, headers=headers, method="POST")
        with urlrequest.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
            raw_payload = json.loads(response.read().decode("utf-8"))
        return self._normalize_response(raw_payload)

    def _build_messages(self, request: LLMRequest) -> list[dict[str, str]]:
        if request.messages:
            return [{"role": msg.role, "content": msg.content} for msg in request.messages]
        built: list[dict[str, str]] = []
        if request.system_prompt:
            built.append({"role": "system", "content": request.system_prompt})
        if request.user_content:
            built.append({"role": "user", "content": request.user_content})
        return built

    def _normalize_response(self, payload: dict[str, Any]) -> LLMResponse:
        choice = (payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content", "")
        usage = payload.get("usage") or {}
        return LLMResponse(
            raw_text=content,
            parsed_json=None,
            messages=[LLMMessage(role="assistant", content=content)],
            usage=LLMUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            provider_metadata={"provider": "openai-compatible", "model": payload.get("model", self.model)},
        )


@dataclass
class OllamaProvider:
    model: str
    base_url: str = "http://localhost:11434"
    timeout: float = 30.0

    def generate(self, request: LLMRequest) -> LLMResponse:
        import json
        from urllib import request as urlrequest

        endpoint = f"{self.base_url.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._build_messages(request),
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlrequest.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
            raw_payload = json.loads(response.read().decode("utf-8"))

        message = raw_payload.get("message") or {}
        content = message.get("content", "")
        prompt_tokens = raw_payload.get("prompt_eval_count", 0)
        completion_tokens = raw_payload.get("eval_count", 0)
        return LLMResponse(
            raw_text=content,
            parsed_json=None,
            messages=[LLMMessage(role="assistant", content=content)],
            usage=LLMUsage(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            provider_metadata={"provider": "ollama", "model": raw_payload.get("model", self.model)},
        )

    def _build_messages(self, request: LLMRequest) -> list[dict[str, str]]:
        if request.messages:
            return [{"role": msg.role, "content": msg.content} for msg in request.messages]
        built: list[dict[str, str]] = []
        if request.system_prompt:
            built.append({"role": "system", "content": request.system_prompt})
        if request.user_content:
            built.append({"role": "user", "content": request.user_content})
        return built


class MockLLMProvider:
    """Deterministic mock provider used by unit tests and local workflows."""

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError(f"mocked transient failure for {request.task_type}")

        payload = {
            "task_type": request.task_type,
            "messages": [message.model_dump() for message in request.messages],
            "system_prompt": request.system_prompt,
            "user_content": request.user_content,
            "call": self.calls,
        }
        return LLMResponse(
            raw_text=str(payload),
            parsed_json=payload,
            usage=LLMUsage(input_tokens=max(1, len(str(request.model_dump())) // 4), output_tokens=max(1, len(str(payload)) // 4), total_tokens=0),
            provider_metadata={"provider": "mock-openai", "call": self.calls},
        )
