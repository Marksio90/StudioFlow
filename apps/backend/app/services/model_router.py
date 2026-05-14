from __future__ import annotations

import os


class ModelRouter:
    """Resolve model names per task type using environment configuration."""

    TASK_MODEL_ENV_MAP = {
        "research": "LLM_RESEARCH_MODEL",
        "script_generation": "LLM_SCRIPT_MODEL",
        "seo_metadata": "LLM_SEO_MODEL",
        "compliance": "LLM_COMPLIANCE_MODEL",
        "classification": "LLM_CLASSIFIER_MODEL",
        "performance_analysis": "LLM_PERFORMANCE_MODEL",
        "summarization": "LLM_SUMMARIZATION_MODEL",
    }

    AGENT_TASK_ALIAS = {
        "researchagent": "research",
        "scriptagent": "script_generation",
        "seoagent": "seo_metadata",
        "complianceagent": "compliance",
        "performanceagent": "performance_analysis",
        "classificationagent": "classification",
        "summarizationagent": "summarization",
    }

    def __init__(self, default_model: str | None = None) -> None:
        self.default_model = default_model or os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")

    def resolve(self, *, task_type: str) -> str:
        normalized_task = self._normalize_task_type(task_type)
        model_env = self.TASK_MODEL_ENV_MAP.get(normalized_task)
        if model_env:
            configured_model = os.getenv(model_env)
            if configured_model:
                return configured_model
        return self.default_model

    def _normalize_task_type(self, task_type: str) -> str:
        cleaned_task_type = task_type.strip()
        alias_key = cleaned_task_type.lower()
        return self.AGENT_TASK_ALIAS.get(alias_key, cleaned_task_type)
