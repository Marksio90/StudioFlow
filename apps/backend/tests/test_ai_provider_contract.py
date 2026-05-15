from app.services.ai_provider import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    MessageConstructor,
    MockLLMProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    UNTRUSTED_USER_PREFIX,
)


def test_provider_message_construction_contract_for_untrusted_input():
    request = LLMRequest(
        task_type="ResearchAgent",
        system_prompt="system",
        messages=[LLMMessage(role="user", content="payload", trusted=False)],
    )
    messages = MessageConstructor.build(request)
    assert messages[0] == {"role": "system", "content": "system"}
    assert messages[1]["content"].startswith(UNTRUSTED_USER_PREFIX)


def test_openai_and_ollama_build_messages_share_interface_contract():
    req = LLMRequest(task_type="ResearchAgent", user_content='{"x":1}')
    openai_messages = OpenAICompatibleProvider(base_url="https://example.test/v1", api_key="x", model="m")._build_messages(req)
    ollama_messages = OllamaProvider(model="m")._build_messages(req)
    assert openai_messages == ollama_messages
    assert openai_messages[0]["role"] == "user"


def test_openai_compatible_response_normalization_contract():
    provider = OpenAICompatibleProvider(base_url="https://example.test/v1", api_key="x", model="gpt-test")
    response = provider._normalize_response(
        {
            "model": "gpt-test",
            "choices": [{"message": {"content": "{\"ok\":true}"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }
    )
    assert isinstance(response, LLMResponse)
    assert response.usage == LLMUsage(input_tokens=10, output_tokens=4, total_tokens=14)
    assert response.provider_metadata["provider"] == "openai-compatible"


def test_mock_provider_is_deterministic_for_same_task_shape():
    provider = MockLLMProvider()
    request = LLMRequest(task_type="ComplianceAgent", user_content="demo")
    first = provider.generate(request)
    second = provider.generate(request)
    assert first.parsed_json == second.parsed_json
    assert second.provider_metadata["call"] == 2
