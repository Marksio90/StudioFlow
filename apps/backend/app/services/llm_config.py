from __future__ import annotations

import os

from pydantic import BaseModel, Field


class LLMRetryConfig(BaseModel):
    attempts: int = Field(default=3, ge=1)
    backoff_seconds: float = Field(default=1.0, ge=0)
    jitter_seconds: float = Field(default=0.1, ge=0)
    retriable_errors: list[str] = Field(default_factory=lambda: ["timeout", "rate_limit", "connection_error"])


class LLMModelConfig(BaseModel):
    provider: str = "openai-compatible"
    model: str
    base_url: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0)
    retry: LLMRetryConfig = Field(default_factory=LLMRetryConfig)

    @classmethod
    def from_env(cls) -> "LLMModelConfig":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "openai-compatible"),
            model=os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            retry=LLMRetryConfig(
                attempts=int(os.getenv("LLM_RETRY_ATTEMPTS", "3")),
                backoff_seconds=float(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "1")),
                jitter_seconds=float(os.getenv("LLM_RETRY_JITTER_SECONDS", "0.1")),
                retriable_errors=[
                    item.strip()
                    for item in os.getenv(
                        "LLM_RETRIABLE_ERRORS", "timeout,rate_limit,connection_error"
                    ).split(",")
                    if item.strip()
                ],
            ),
        )
