import pytest

from app.services.product_agents import (
    AgentExecutionError,
    ComplianceInput,
    MockLLMProvider,
    NoopCostTracker,
    PerformanceInput,
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


def test_all_agents_return_structured_json_models():
    provider = MockLLMProvider()
    tracker = NoopCostTracker()
    workflow = ProductWorkflow(provider, cost_tracker=tracker)
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


def test_retry_policy_handles_transient_failures():
    provider = MockLLMProvider(failures_before_success=1)
    workflow = ProductWorkflow(provider, retry=RetryPolicy(max_attempts=2))
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
    workflow = ProductWorkflow(provider, retry=RetryPolicy(max_attempts=2))
    research, script, seo, compliance, performance = _inputs()

    with pytest.raises(AgentExecutionError):
        workflow.run(
            research_input=research,
            script_input=script,
            seo_input=seo,
            compliance_input=compliance,
            performance_input=performance,
        )
