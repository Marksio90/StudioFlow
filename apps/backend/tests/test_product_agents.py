import pytest
from uuid import uuid4

from app.services.product_agents import (
    AgentExecutionError,
    ComplianceInput,
    MockLLMProvider,
    NoopCostTracker,
    PerformanceInput,
    LLMRequestContext,
    ProductWorkflow,
    ResearchInput,
    RetryPolicy,
    SEOInput,
    ScriptInput,
)


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
