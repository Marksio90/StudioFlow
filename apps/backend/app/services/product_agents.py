from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, Field


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot produce a valid structured output."""


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)


@dataclass
class CostEvent:
    agent_name: str
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: Decimal


class CostTracker(Protocol):
    def record(self, event: CostEvent) -> None: ...


class NoopCostTracker:
    def __init__(self) -> None:
        self.events: list[CostEvent] = []

    def record(self, event: CostEvent) -> None:
        self.events.append(event)


class MockLLMProvider:
    """Deterministic mock provider used by unit tests and local workflows."""

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def generate(self, *, agent_name: str, payload: dict) -> dict:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError(f"mocked transient failure for {agent_name}")

        # Echoes payload into a predictable envelope that each agent maps to schema.
        return {"agent_name": agent_name, "payload": payload, "call": self.calls}


class BaseAgent:
    name = "base"

    def __init__(self, provider: MockLLMProvider, retry: RetryPolicy | None = None, cost_tracker: CostTracker | None = None) -> None:
        self.provider = provider
        self.retry = retry or RetryPolicy()
        self.cost_tracker = cost_tracker or NoopCostTracker()

    def _generate(self, payload: dict) -> dict:
        last_error: Exception | None = None
        for _ in range(self.retry.max_attempts):
            try:
                raw = self.provider.generate(agent_name=self.name, payload=payload)
                self.cost_tracker.record(
                    CostEvent(
                        agent_name=self.name,
                        prompt_tokens=120,
                        completion_tokens=240,
                        total_cost_usd=Decimal("0.0012"),
                    )
                )
                return raw
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise AgentExecutionError(f"{self.name} failed after {self.retry.max_attempts} attempts") from last_error


class ResearchInput(BaseModel):
    channel_profile: str
    target_audience: str
    topic: str
    language: str
    previous_videos: list[str]
    analytics_snapshot: dict


class ResearchOutput(BaseModel):
    video_ideas: list[str]
    angles: list[str]
    search_intent: str
    target_audience: str
    risk_notes: list[str]


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"

    def run(self, data: ResearchInput) -> ResearchOutput:
        raw = self._generate(data.model_dump())
        return ResearchOutput(
            video_ideas=[f"{data.topic} - format 1", f"{data.topic} - format 2"],
            angles=["problem/solution", "case study"],
            search_intent=f"Użytkownik chce zrozumieć: {data.topic}",
            target_audience=data.target_audience,
            risk_notes=[f"mock_call={raw['call']}", "zweryfikować źródła danych"],
        )


class ScriptInput(BaseModel):
    selected_idea: str
    research_context: dict
    tone: str
    language: str
    target_duration: int = Field(ge=30, le=3600)


class ScriptOutput(BaseModel):
    hook: str
    outline: list[str]
    full_script: str
    cta: str
    chapters: list[str]


class ScriptAgent(BaseAgent):
    name = "ScriptAgent"

    def run(self, data: ScriptInput) -> ScriptOutput:
        self._generate(data.model_dump())
        return ScriptOutput(
            hook=f"Czy wiesz, dlaczego {data.selected_idea}?",
            outline=["Intro", "Problem", "Rozwiązanie", "Podsumowanie"],
            full_script=f"[{data.tone}] Skrypt dla: {data.selected_idea}",
            cta="Napisz w komentarzu, co testujesz jako następne.",
            chapters=["00:00 Intro", "00:40 Problem", "02:00 Rozwiązanie", "03:30 CTA"],
        )


class SEOInput(BaseModel):
    topic: str
    script: str
    language: str


class SEOOutput(BaseModel):
    title_variants: list[str]
    description: str
    tags: list[str]
    thumbnail_brief: str
    chapters: list[str]
    pinned_comment: str


class SEOAgent(BaseAgent):
    name = "SEOAgent"

    def run(self, data: SEOInput) -> SEOOutput:
        self._generate(data.model_dump())
        return SEOOutput(
            title_variants=[f"{data.topic}: kompletny przewodnik", f"{data.topic} w 5 krokach"],
            description=f"Materiał o {data.topic} w języku {data.language}.",
            tags=[data.topic, "youtube seo", "content strategy"],
            thumbnail_brief="Kontrastowe tło, 3 słowa, emocjonalna twarz.",
            chapters=["00:00 Start", "01:00 Wartość", "03:00 Wnioski"],
            pinned_comment="Jaki temat rozwinąć w kolejnym odcinku?",
        )


class ComplianceInput(BaseModel):
    script: str
    claims: list[str]


class ComplianceOutput(BaseModel):
    risk_level: str
    score: int = Field(ge=0, le=100)
    requires_ai_disclosure: bool
    reasons: list[str]
    recommendations: list[str]
    blocking_issues: list[str]


class ComplianceAgent(BaseAgent):
    name = "ComplianceAgent"

    def run(self, data: ComplianceInput) -> ComplianceOutput:
        self._generate(data.model_dump())
        return ComplianceOutput(
            risk_level="low",
            score=92,
            requires_ai_disclosure=True,
            reasons=["Skrypt zawiera treści generowane automatycznie."],
            recommendations=["Dodaj disclosure AI w opisie."],
            blocking_issues=[],
        )


class PerformanceInput(BaseModel):
    analytics_snapshot: dict
    video_metadata: dict
    script: str
    previous_performance: list[dict]


class PerformanceOutput(BaseModel):
    what_worked: list[str]
    what_failed: list[str]
    next_recommendations: list[str]
    title_thumbnail_suggestions: list[str]


class PerformanceAgent(BaseAgent):
    name = "PerformanceAgent"

    def run(self, data: PerformanceInput) -> PerformanceOutput:
        self._generate(data.model_dump())
        return PerformanceOutput(
            what_worked=["Mocny hook zwiększył CTR."],
            what_failed=["Za długi segment środkowy obniżył retencję."],
            next_recommendations=["Skróć część środkową o 20%.", "Dodaj pattern interrupt po 45s."],
            title_thumbnail_suggestions=["Wersja tytułu z liczbą", "Miniatura z kontrastowym hasłem"],
        )


class ProductWorkflowResult(BaseModel):
    research: ResearchOutput
    script: ScriptOutput
    seo: SEOOutput
    compliance: ComplianceOutput
    performance: PerformanceOutput


class ProductWorkflow:
    def __init__(self, provider: MockLLMProvider, retry: RetryPolicy | None = None, cost_tracker: CostTracker | None = None) -> None:
        self.research = ResearchAgent(provider, retry=retry, cost_tracker=cost_tracker)
        self.script = ScriptAgent(provider, retry=retry, cost_tracker=cost_tracker)
        self.seo = SEOAgent(provider, retry=retry, cost_tracker=cost_tracker)
        self.compliance = ComplianceAgent(provider, retry=retry, cost_tracker=cost_tracker)
        self.performance = PerformanceAgent(provider, retry=retry, cost_tracker=cost_tracker)

    def run(self, *, research_input: ResearchInput, script_input: ScriptInput, seo_input: SEOInput, compliance_input: ComplianceInput, performance_input: PerformanceInput) -> ProductWorkflowResult:
        research = self.research.run(research_input)
        script = self.script.run(script_input)
        seo = self.seo.run(seo_input)
        compliance = self.compliance.run(compliance_input)
        performance = self.performance.run(performance_input)
        return ProductWorkflowResult(
            research=research,
            script=script,
            seo=seo,
            compliance=compliance,
            performance=performance,
        )
