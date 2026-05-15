from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str
    content: str
    trusted: bool = True


class LLMRequest(BaseModel):
    task_type: str
    messages: list[LLMMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    user_content: str | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


UNTRUSTED_USER_PREFIX = "[UNTRUSTED USER CONTENT]\n"


class MessageConstructor:
    """Construct provider messages while preserving trust boundaries."""

    @staticmethod
    def build(request: LLMRequest) -> list[dict[str, str]]:
        built: list[dict[str, str]] = []
        if request.system_prompt:
            built.append({"role": "system", "content": request.system_prompt})
        if request.messages:
            for msg in request.messages:
                built.append({"role": msg.role, "content": MessageConstructor._render_content(msg)})
            return built
        if request.user_content:
            built.append({"role": "user", "content": UNTRUSTED_USER_PREFIX + request.user_content})
        return built

    @staticmethod
    def _render_content(message: LLMMessage) -> str:
        if message.role == "user" and not message.trusted:
            return UNTRUSTED_USER_PREFIX + message.content
        return message.content


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
        return MessageConstructor.build(request)

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
        return MessageConstructor.build(request)


class MockLLMProvider:
    """Deterministic mock provider used by unit tests and local workflows."""

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError(f"mocked transient failure for {request.task_type}")

        payload = self._build_structured_payload(request)
        return LLMResponse(
            raw_text=str(payload),
            parsed_json=payload,
            usage=LLMUsage(input_tokens=max(1, len(str(request.model_dump())) // 4), output_tokens=max(1, len(str(payload)) // 4), total_tokens=0),
            provider_metadata={"provider": "mock-openai", "call": self.calls},
        )

    def _build_structured_payload(self, request: LLMRequest) -> dict[str, Any]:
        task = request.task_type
        if task == "ResearchAgent":
            return {
                "video_ideas": ["LLM observability - format 1", "LLM observability - format 2"],
                "angles": ["problem/solution", "case study"],
                "search_intent": "Użytkownik chce zrozumieć: LLM observability",
                "target_audience": "Junior AI Engineers",
                "risk_notes": [f"mock_call={self.calls}", "zweryfikować źródła danych"],
            }
        if task == "ScriptAgent":
            return {
                "hook": "Czy wiesz, dlaczego LLM observability - format 1?",
                "outline": ["Intro", "Problem", "Rozwiązanie", "Podsumowanie"],
                "full_script": "[expert] Skrypt dla: LLM observability - format 1",
                "cta": "Napisz w komentarzu, co testujesz jako następne.",
                "chapters": ["00:00 Intro", "00:40 Problem", "02:00 Rozwiązanie", "03:30 CTA"],
            }
        if task == "SEOAgent":
            return {
                "title_variants": ["LLM observability: kompletny przewodnik", "LLM observability w 5 krokach"],
                "description": "Materiał o LLM observability w języku pl.",
                "tags": ["LLM observability", "youtube seo", "content strategy"],
                "thumbnail_brief": "Kontrastowe tło, 3 słowa, emocjonalna twarz.",
                "chapters": ["00:00 Start", "01:00 Wartość", "03:00 Wnioski"],
                "pinned_comment": "Jaki temat rozwinąć w kolejnym odcinku?",
            }
        if task == "ComplianceAgent":
            return {
                "risk_level": "low",
                "score": 92,
                "requires_ai_disclosure": True,
                "reasons": ["Skrypt zawiera treści generowane automatycznie."],
                "recommendations": ["Dodaj disclosure AI w opisie."],
                "blocking_issues": [],
            }
        if task == "PerformanceAgent":
            return {
                "what_worked": ["Dobry hook w pierwszych 30 sekundach"],
                "what_failed": ["Niski retention w środku filmu"],
                "next_recommendations": ["Skrócić segment problemowy"],
                "title_thumbnail_suggestions": ["Mocniejszy kontrast miniatury"],
            }
        if task == "NicheIntelligenceAgent":
            return {
                "summary": "Niche has solid demand with moderate competition and strong room for distinct positioning.",
                "score_explanations": {"demand_score": "Consistent audience pull in the niche cluster.", "competition_score": "Established players exist but gaps remain."},
                "strengths": ["Clear audience pain points", "Repeatable topic stream"],
                "weaknesses": ["Crowded keyword surface"],
                "risks": ["Potential policy sensitivity in claims"],
                "recommended_positioning": "Practical, evidence-led tutorials for intermediate creators.",
                "content_pillar_suggestions": ["How-to breakdowns", "Case-study deconstructions", "Tooling workflows"],
                "differentiation_opportunities": ["Original framework naming", "Before/after teardown series"],
                "compliance_notes": ["Avoid guaranteed income claims", "Use clear AI disclosure when synthetic assets are used"],
                "next_actions": ["Validate with 10 pilot topics", "Run audience objection interviews"],
                "scores": {"demand_score": 78, "competition_score": 64, "originality_potential": 81, "production_difficulty": 57, "monetization_potential": 69, "compliance_risk": 35, "long_term_depth": 76, "overall_score": 74}
            }
        return {"task_type": task, "call": self.calls}
