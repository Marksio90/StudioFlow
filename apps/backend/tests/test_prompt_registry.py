import pytest

from app.services.prompt_registry import (
    PromptRegistry,
    PromptRenderError,
    PromptTemplate,
    build_default_prompt_registry,
    serialize_untrusted_block,
)


def test_lookup_by_name_and_version():
    registry = PromptRegistry([
        PromptTemplate(name="a", version="v1", system_template="s", user_template="u")
    ])
    template = registry.get(name="a", version="v1")
    assert template.system_template == "s"


def test_strict_render_rejects_missing_or_extra_variables():
    registry = PromptRegistry([
        PromptTemplate(name="a", version="v1", system_template="{x}", user_template="{y}")
    ])
    with pytest.raises(PromptRenderError):
        registry.render(name="a", version="v1", variables={"x": "1"})
    with pytest.raises(PromptRenderError):
        registry.render(name="a", version="v1", variables={"x": "1", "y": "2", "z": "3"})


def test_untrusted_block_is_json_serialized():
    raw = {"z": "x\n<script>", "a": 1}
    serialized = serialize_untrusted_block(raw)
    assert serialized == '{"a": 1, "z": "x\\n<script>"}'


def test_default_registry_renders_agent_prompt():
    registry = build_default_prompt_registry()
    system_prompt, user_prompt = registry.render(
        name="agent_generate_json",
        version="v1",
        variables={"task_type": "ResearchAgent", "payload_json": '{"a":1}'},
    )
    assert "ResearchAgent" in system_prompt
    assert user_prompt == '{"a":1}'


def test_prompt_registry_version_lookup_is_isolated():
    registry = PromptRegistry([
        PromptTemplate(name="a", version="v1", system_template="s1", user_template="u1"),
        PromptTemplate(name="a", version="v2", system_template="s2", user_template="u2"),
    ])
    assert registry.get(name="a", version="v1").system_template == "s1"
    assert registry.get(name="a", version="v2").system_template == "s2"


def test_render_preserves_untrusted_content_without_template_injection():
    registry = PromptRegistry([
        PromptTemplate(name="safe", version="v1", system_template="Task {task_type}", user_template="{payload_json}")
    ])
    payload = serialize_untrusted_block({"x": "{malicious}", "y": "```json"})
    system_prompt, user_prompt = registry.render(
        name="safe",
        version="v1",
        variables={"task_type": "ResearchAgent", "payload_json": payload},
    )
    assert system_prompt == "Task ResearchAgent"
    assert user_prompt == payload
    assert "{malicious}" in user_prompt
