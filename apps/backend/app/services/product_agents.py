from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import re
from time import perf_counter
from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest, MockLLMProvider
from app.services.model_router import ModelRouter


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot produce a valid structured output."""

@dataclass
class LLMErrorContext:
    provider: str
    model: str
    task_type: str
    trace_id: str


class LLMProviderError(AgentExecutionError):
    def __init__(self, message: str, context: LLMErrorContext) -> None:
        super().__init__(f"{message} provider={context.provider} model={context.model} task={context.task_type} trace={context.trace_id}")
        self.context = context


class LLMParseError(AgentExecutionError):
    def __init__(self, message: str, context: LLMErrorContext, raw_output: str) -> None:
        super().__init__(f"{message} provider={context.provider} model={context.model} task={context.task_type} trace={context.trace_id}")
        self.context = context
        self.raw_output = raw_output


class LLMSchemaValidationError(AgentExecutionError):
    def __init__(self, message: str, context: LLMErrorContext, validation_error: ValidationError) -> None:
        super().__init__(f"{message} provider={context.provider} model={context.model} task={context.task_type} trace={context.trace_id}")
        self.context = context
        self.validation_error = validation_error


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
    def record_failure(self, event: dict[str, Any]) -> None: ...


class NoopCostTracker:
    def __init__(self) -> None:
        self.events: list[LLMCallRecord] = []

    def record(self, event: LLMCallRecord) -> None:
        self.events.append(event)

    def record_failure(self, event: dict[str, Any]) -> None:
        return None


@dataclass
class LLMRequestContext:
    organization_id: UUID
    workspace_id: UUID
    video_project_id: UUID
    workflow_run_id: UUID | None


class TrackedLLMClient:
    def __init__(self, provider: LLMProvider, model_router: ModelRouter | None = None, cost_tracker: CostTracker | None = None) -> None:
        self.provider = provider
        self.model_router = model_router or ModelRouter()
        self.cost_tracker = cost_tracker or NoopCostTracker()

    def generate(self, *, task_type: str, payload: dict, context: LLMRequestContext) -> dict[str, Any]:
        return self._generate_dict(task_type=task_type, payload=payload, context=context)

    def _generate_dict(self, *, task_type: str, payload: dict, context: LLMRequestContext, repair_input: str | None = None) -> dict[str, Any]:
        started = perf_counter()
        llm_config = self.model_router.resolve(task_type=task_type)
        if repair_input is None:
            user_payload = str(payload)
            messages = [LLMMessage(role="user", content=user_payload)]
            system_prompt = f"Task: {task_type}. Return valid JSON only."
        else:
            user_payload = repair_input
            messages = [LLMMessage(role="user", content=repair_input)]
            system_prompt = "Repair the following content into valid JSON only. Return JSON with no markdown."
        request = LLMRequest(
            task_type=task_type,
            system_prompt=system_prompt,
            user_content=user_payload,
            messages=messages,
            provider_metadata={"task_type": task_type, "response_format": "json"},
        )
        trace_id = sha256(f"{task_type}:{payload}:{context.workflow_run_id}".encode()).hexdigest()[:16]
        try:
            response = self.provider.generate(request)
        except Exception as exc:  # noqa: BLE001
            self.cost_tracker.record_failure(
                {
                    "provider": llm_config.provider,
                    "model": llm_config.model,
                    "prompt_template_name": task_type,
                    "input_hash": sha256(str(payload).encode()).hexdigest(),
                    "status": "failed",
                    "error_message": str(exc),
                    "trace_id": trace_id,
                    "related_entity_type": "workflow_run",
                    "related_entity_id": context.workflow_run_id,
                }
            )
            raise LLMProviderError(
                "LLM provider request failed",
                context=LLMErrorContext(provider=llm_config.provider, model=llm_config.model, task_type=task_type, trace_id=trace_id),
            ) from exc
        raw = response.parsed_json
        if raw is None:
            raw = self._parse_json_response(response.raw_text)
        if raw is None and repair_input is None:
            repaired = self._generate_dict(
                task_type=task_type,
                payload=payload,
                context=context,
                repair_input=f"Return strict JSON only for this task payload.\n{payload}\nPrevious invalid output:\n{response.raw_text}",
            )
            raw = repaired
        if raw is None:
            self.cost_tracker.record_failure(
                {
                    "provider": llm_config.provider,
                    "model": llm_config.model,
                    "prompt_template_name": task_type,
                    "input_hash": sha256(str(payload).encode()).hexdigest(),
                    "output_hash": sha256((response.raw_text or "").encode()).hexdigest(),
                    "status": "failed",
                    "error_message": "Failed to parse model output as JSON",
                    "trace_id": trace_id,
                    "related_entity_type": "workflow_run",
                    "related_entity_id": context.workflow_run_id,
                }
            )
            raise LLMParseError(
                "Failed to parse model output as JSON",
                context=LLMErrorContext(provider=llm_config.provider, model=llm_config.model, task_type=task_type, trace_id=trace_id),
                raw_output=response.raw_text,
            )
        latency_ms = int((perf_counter() - started) * 1000)
        input_tokens = max(1, len(str(payload)) // 4)
        output_tokens = response.usage.output_tokens or max(1, len(str(raw)) // 4)
        est_cost = Decimal(input_tokens * 0.0000002 + output_tokens * 0.0000008).quantize(Decimal("0.00000001"))
        request_hash = sha256(f"{task_type}:{payload}".encode()).hexdigest()
        self.cost_tracker.record(LLMCallRecord(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            video_project_id=context.video_project_id,
            workflow_run_id=context.workflow_run_id,
            provider=response.provider_metadata.get("provider", "unknown"),
            model=llm_config.model,
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

    def _parse_json_response(self, text: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

class BaseAgent:
    name = "base"

    def __init__(self, llm_client: TrackedLLMClient, context: LLMRequestContext, retry: RetryPolicy | None = None) -> None:
        self.llm_client = llm_client
        self.context = context
        self.retry = retry or RetryPolicy()

    TModel = TypeVar("TModel", bound=BaseModel)

    def _generate_typed(self, payload: dict, output_model: type[TModel]) -> TModel:
        last_error: Exception | None = None
        for _ in range(self.retry.max_attempts):
            try:
                raw = self.llm_client.generate(task_type=self.name, payload=payload, context=self.context)
                return output_model.model_validate(raw)
            except ValidationError as exc:
                last_error = LLMSchemaValidationError(
                    "LLM output schema validation failed",
                    context=LLMErrorContext(
                        provider=self.llm_client.model_router.resolve(task_type=self.name).provider,
                        model=self.llm_client.model_router.resolve(task_type=self.name).model,
                        task_type=self.name,
                        trace_id=sha256(f"{self.name}:{payload}:{self.context.workflow_run_id}".encode()).hexdigest()[:16],
                    ),
                    validation_error=exc,
                )
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
        return self._generate_typed(data.model_dump(), ResearchOutput)


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
        return self._generate_typed(data.model_dump(), ScriptOutput)


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
        return self._generate_typed(data.model_dump(), SEOOutput)


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
        return self._generate_typed(data.model_dump(), ComplianceOutput)


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
        return self._generate_typed(data.model_dump(), PerformanceOutput)


class ProductWorkflowResult(BaseModel):
    research: ResearchOutput
    script: ScriptOutput
    seo: SEOOutput
    compliance: ComplianceOutput
    performance: PerformanceOutput


class ProductWorkflow:
    def __init__(self, provider: LLMProvider, context: LLMRequestContext, retry: RetryPolicy | None = None, cost_tracker: CostTracker | None = None) -> None:
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
