from app.services.model_router import ModelRouter


def test_seo_metadata_uses_seo_model(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="seo_metadata") == "seo-model"


def test_compliance_uses_compliance_model(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_COMPLIANCE_MODEL", "compliance-model")

    router = ModelRouter()

    assert router.resolve(task_type="compliance") == "compliance-model"


def test_missing_configuration_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("LLM_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("LLM_SEO_MODEL", raising=False)

    router = ModelRouter()

    assert router.resolve(task_type="seo_metadata") == "gpt-4o-mini"
    assert router.resolve(task_type="unknown_task") == "gpt-4o-mini"


def test_agent_names_are_mapped_to_task_types(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="SEOAgent") == "seo-model"



def test_task_type_whitespace_is_trimmed(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_SEO_MODEL", "seo-model")

    router = ModelRouter()

    assert router.resolve(task_type="  seo_metadata  ") == "seo-model"


def test_agent_alias_mapping_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "default-model")
    monkeypatch.setenv("LLM_COMPLIANCE_MODEL", "compliance-model")

    router = ModelRouter()

    assert router.resolve(task_type="complianceagent") == "compliance-model"
    assert router.resolve(task_type="ComplianceAgent") == "compliance-model"
