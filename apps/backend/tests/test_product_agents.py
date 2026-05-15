import pytest
from uuid import uuid4

from app.services.product_agents import (
    AgentExecutionError,
    LLMParseError,
    LLMRequestContext,
    LLMSchemaValidationError,
    ComplianceInput,
    ProductWorkflow,
    ResearchInput,
    RetryPolicy,
    SEOInput,
    ScriptInput,
    TrackedLLMClient,
    ResearchAgent,
    NoopCostTracker,
    MockLLMProvider,
    PerformanceInput,
)
from app.services.ai_provider import LLMProvider, LLMRequest, LLMResponse, LLMUsage


def _inputs():
    research = ResearchInput(
        channel_profile="Tech edukacja",
        target_audience="Junior AI Engineers",
        topic="LLM observability",
        language="pl",
        previous_videos=["Prompt basics", "RAG intro"],
        analytics_snapshot={"ctr": 0.06},
    )
    script = ScriptInput(
        selected_idea="LLM observability - format 1",
        research_context=research.model_dump(),
        tone="expert",
        language="pl",
        target_duration=300,
    )
    seo = SEOInput(topic=research.topic, script="demo", language="pl")
    compliance = ComplianceInput(script="demo", claims=["100% accuracy"])
    performance = PerformanceInput(
        analytics_snapshot={"retention": 0.45},
        video_metadata={"title": "x"},
        script="demo",
        previous_performance=[{"views": 1000}],
    )
    return research, script, seo, compliance, performance


def _context():
    return LLMRequestContext(organization_id=uuid4(), workspace_id=uuid4(), video_project_id=uuid4(), workflow_run_id=uuid4())


def test_all_agents_return_structured_json_models():
    provider = MockLLMProvider()
    tracker = NoopCostTracker()
    workflow = ProductWorkflow(provider, context=_context(), cost_tracker=tracker)
    research, script, seo, compliance, performance = _inputs()

    result = workflow.run(
        research_input=research,
        script_input=script,
        seo_input=seo,
        compliance_input=compliance,
        performance_input=performance,
    )

    payload = result.model_dump()
    assert set(payload.keys()) == {"research", "script", "seo", "compliance", "performance"}
    assert isinstance(payload["research"]["video_ideas"], list)
    assert isinstance(payload["script"]["full_script"], str)
    assert isinstance(payload["seo"]["tags"], list)
    assert isinstance(payload["compliance"]["blocking_issues"], list)
    assert isinstance(payload["performance"]["what_worked"], list)
    assert len(tracker.events) == 5
    agent_names = {e.task_type for e in tracker.events}
    assert {"ResearchAgent", "ScriptAgent", "SEOAgent", "ComplianceAgent"}.issubset(agent_names)
    first = tracker.events[0]
    assert first.organization_id
    assert first.workspace_id
    assert first.video_project_id
    assert first.workflow_run_id
    assert first.provider
    assert first.model
    assert first.input_tokens > 0
    assert first.output_tokens > 0
    assert first.estimated_cost > 0
    assert len(first.request_hash) == 64


def test_retry_policy_handles_transient_failures():
    provider = MockLLMProvider(failures_before_success=1)
    workflow = ProductWorkflow(provider, context=_context(), retry=RetryPolicy(max_attempts=2))
    research, script, seo, compliance, performance = _inputs()

    result = workflow.run(
        research_input=research,
        script_input=script,
        seo_input=seo,
        compliance_input=compliance,
        performance_input=performance,
    )

    assert result.compliance.score == 92


def test_retry_policy_raises_after_exhaustion():
    provider = MockLLMProvider(failures_before_success=99)
    workflow = ProductWorkflow(provider, context=_context(), retry=RetryPolicy(max_attempts=2))
    research, script, seo, compliance, performance = _inputs()

    with pytest.raises(AgentExecutionError):
        workflow.run(
            research_input=research,
            script_input=script,
            seo_input=seo,
            compliance_input=compliance,
            performance_input=performance,
        )


class _MalformedThenValidProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(raw_text='{"video_ideas": [}', parsed_json=None, usage=LLMUsage(output_tokens=10))
        return LLMResponse(
            raw_text='{"video_ideas":["a"],"angles":["b"],"search_intent":"c","target_audience":"d","risk_notes":["e"]}',
            parsed_json=None,
            usage=LLMUsage(output_tokens=10),
            provider_metadata={"provider": "test-provider"},
        )


class _InvalidSchemaProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(raw_text='{"video_ideas":"not-a-list"}', parsed_json=None, usage=LLMUsage(output_tokens=10))


class _AlwaysMalformedProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(raw_text='{"video_ideas": [}', parsed_json=None, usage=LLMUsage(output_tokens=10))


class _RecordingCostTracker(NoopCostTracker):
    def __init__(self) -> None:
        super().__init__()
        self.failures: list[dict] = []

    def record_failure(self, event: dict) -> None:
        self.failures.append(event)


class _SecretFailureProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise RuntimeError("api_key=super-secret password=hunter2")


def test_structured_generation_recovers_once_from_malformed_json():
    client = TrackedLLMClient(_MalformedThenValidProvider())
    agent = ResearchAgent(client, context=_context())
    output = agent.run(_inputs()[0])
    assert output.video_ideas == ["a"]


def test_structured_generation_raises_schema_validation_error():
    client = TrackedLLMClient(_InvalidSchemaProvider())
    agent = ResearchAgent(client, context=_context(), retry=RetryPolicy(max_attempts=1))
    with pytest.raises(AgentExecutionError) as exc:
        agent.run(_inputs()[0])
    assert isinstance(exc.value.__cause__, LLMSchemaValidationError | LLMParseError)


def test_malformed_json_recovery_path_exhausts_and_raises_parse_error():
    client = TrackedLLMClient(_AlwaysMalformedProvider())
    agent = ResearchAgent(client, context=_context(), retry=RetryPolicy(max_attempts=1))
    with pytest.raises(AgentExecutionError) as exc:
        agent.run(_inputs()[0])
    assert isinstance(exc.value.__cause__, LLMParseError)


def test_llm_call_failure_logging_is_complete_and_redacted():
    tracker = _RecordingCostTracker()
    client = TrackedLLMClient(_SecretFailureProvider(), cost_tracker=tracker)
    agent = ResearchAgent(client, context=_context(), retry=RetryPolicy(max_attempts=1))
    with pytest.raises(AgentExecutionError):
        agent.run(_inputs()[0])
    assert len(tracker.failures) == 1
    failure = tracker.failures[0]
    assert failure["status"] == "failed"
    assert failure["provider"]
    assert failure["model"]
    assert failure["trace_id"]
    assert failure["related_entity_type"] == "workflow_run"
    assert "super-secret" not in failure["error_message"]
    assert "hunter2" not in failure["error_message"]
