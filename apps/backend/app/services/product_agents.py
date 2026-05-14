from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from time import perf_counter
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot produce a valid structured output."""


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)


@dataclass
class LLMCallRecord:
    organization_id: UUID
    workspace_id: UUID
    video_project_id: UUID
    workflow_run_id: UUID | None
    provider: str
    model: str
    task_type: str
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal
    latency_ms: int
    cache_hit: bool
    request_hash: str
    created_at: datetime


class CostTracker(Protocol):
    def record(self, event: LLMCallRecord) -> None: ...


class NoopCostTracker:
    def __init__(self) -> None:
        self.events: list[LLMCallRecord] = []

    def record(self, event: LLMCallRecord) -> None:
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




class ModelRouter:
    def resolve(self, *, task_type: str) -> str:
        mapping = {
            "ResearchAgent": "gpt-4.1-mini",
            "ScriptAgent": "gpt-4.1",
            "SEOAgent": "gpt-4.1-mini",
            "ComplianceAgent": "gpt-4.1-mini",
            "PerformanceAgent": "gpt-4.1-mini",
        }
        return mapping.get(task_type, "gpt-4.1-mini")


@dataclass
class LLMRequestContext:
    organization_id: UUID
    workspace_id: UUID
    video_project_id: UUID
    workflow_run_id: UUID | None


class TrackedLLMClient:
    def __init__(self, provider: MockLLMProvider, model_router: ModelRouter | None = None, cost_tracker: CostTracker | None = None) -> None:
        self.provider = provider
        self.model_router = model_router or ModelRouter()
        self.cost_tracker = cost_tracker or NoopCostTracker()

    def generate(self, *, task_type: str, payload: dict, context: LLMRequestContext) -> dict:
        started = perf_counter()
        raw = self.provider.generate(agent_name=task_type, payload=payload)
        latency_ms = int((perf_counter() - started) * 1000)
        model = self.model_router.resolve(task_type=task_type)
        input_tokens = max(1, len(str(payload)) // 4)
        output_tokens = max(1, len(str(raw)) // 4)
        est_cost = Decimal(input_tokens * 0.0000002 + output_tokens * 0.0000008).quantize(Decimal("0.00000001"))
        request_hash = sha256(f"{task_type}:{payload}".encode()).hexdigest()
        self.cost_tracker.record(LLMCallRecord(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            video_project_id=context.video_project_id,
            workflow_run_id=context.workflow_run_id,
            provider="mock-openai",
            model=model,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=est_cost,
            latency_ms=latency_ms,
            cache_hit=False,
            request_hash=request_hash,
            created_at=datetime.now(timezone.utc),
        ))
        return raw

class BaseAgent:
    name = "base"

    def __init__(self, llm_client: TrackedLLMClient, context: LLMRequestContext, retry: RetryPolicy | None = None) -> None:
        self.llm_client = llm_client
        self.context = context
        self.retry = retry or RetryPolicy()

    def _generate(self, payload: dict) -> dict:
        last_error: Exception | None = None
        for _ in range(self.retry.max_attempts):
            try:
                return self.llm_client.generate(task_type=self.name, payload=payload, context=self.context)
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
    def __init__(self, provider: MockLLMProvider, context: LLMRequestContext, retry: RetryPolicy | None = None, cost_tracker: CostTracker | None = None) -> None:
        tracked = TrackedLLMClient(provider, model_router=ModelRouter(), cost_tracker=cost_tracker)
        self.research = ResearchAgent(tracked, context=context, retry=retry)
        self.script = ScriptAgent(tracked, context=context, retry=retry)
        self.seo = SEOAgent(tracked, context=context, retry=retry)
        self.compliance = ComplianceAgent(tracked, context=context, retry=retry)
        self.performance = PerformanceAgent(tracked, context=context, retry=retry)

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
