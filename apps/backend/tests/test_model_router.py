from app.services.model_router import ModelRouter


def test_seo_metadata_uses_seo_model(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="seo_metadata").model == "seo-model"


def test_compliance_uses_compliance_model(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_COMPLIANCE_MODEL", "compliance-model")

    router = ModelRouter()

    assert router.resolve(task_type="compliance").model == "compliance-model"


def test_missing_configuration_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("LLM_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("LLM_SEO_MODEL", raising=False)

    router = ModelRouter()

    assert router.resolve(task_type="seo_metadata").model == "gpt-4o-mini"
    assert router.resolve(task_type="unknown_task").model == "gpt-4o-mini"


def test_agent_names_are_mapped_to_task_types(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="SEOAgent").model == "seo-model"


def test_task_type_whitespace_is_trimmed(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="  seo_metadata  ").model == "seo-model"


def test_agent_alias_mapping_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_COMPLIANCE_MODEL", "compliance-model")

    router = ModelRouter()

    assert router.resolve(task_type="complianceagent").model == "compliance-model"
    assert router.resolve(task_type="ComplianceAgent").model == "compliance-model"


def test_openai_compatible_profile(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai-compatible")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.3")
    monkeypatch.setenv("LLM_MAX_TOKENS", "2000")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("LLM_RETRY_ATTEMPTS", "4")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_SECONDS", "2")
    monkeypatch.setenv("LLM_RETRY_JITTER_SECONDS", "0.5")
    monkeypatch.setenv("LLM_RETRIABLE_ERRORS", "timeout,rate_limit")

    config = ModelRouter().resolve(task_type="research")

    assert config.provider == "openai-compatible"
    assert config.model == "gpt-4.1-mini"
    assert config.base_url == "https://api.openai.com/v1"
    assert config.temperature == 0.3
    assert config.max_tokens == 2000
    assert config.timeout_seconds == 45
    assert config.retry.attempts == 4
    assert config.retry.backoff_seconds == 2
    assert config.retry.jitter_seconds == 0.5
    assert config.retry.retriable_errors == ["timeout", "rate_limit"]


def test_ollama_local_profile_with_task_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "llama3.1")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_SCRIPT_MODEL", "qwen2.5:14b")

    config = ModelRouter().resolve(task_type="script_generation")

    assert config.provider == "ollama"
    assert config.base_url == "http://localhost:11434/v1"
    assert config.model == "qwen2.5:14b"
