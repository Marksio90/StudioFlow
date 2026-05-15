from __future__ import annotations

from dataclasses import dataclass
import json
from string import Formatter
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system_template: str
    user_template: str


class PromptNotFoundError(KeyError):
    pass


class PromptRenderError(ValueError):
    pass


class PromptRegistry:
    def __init__(self, templates: list[PromptTemplate] | None = None) -> None:
        self._templates: dict[tuple[str, str], PromptTemplate] = {}
        for template in templates or []:
            self.register(template)

    def register(self, template: PromptTemplate) -> None:
        self._templates[(template.name, template.version)] = template

    def get(self, *, name: str, version: str) -> PromptTemplate:
        template = self._templates.get((name, version))
        if template is None:
            raise PromptNotFoundError(f"Prompt template not found: name={name} version={version}")
        return template

    def render(self, *, name: str, version: str, variables: dict[str, Any]) -> tuple[str, str]:
        template = self.get(name=name, version=version)
        system_required = self._required_fields(template.system_template)
        user_required = self._required_fields(template.user_template)
        allowed = system_required | user_required
        provided = set(variables)
        missing = allowed - provided
        extra = provided - allowed
        if missing or extra:
            raise PromptRenderError(
                f"Prompt variable mismatch: missing={sorted(missing)} extra={sorted(extra)}"
            )
        system_prompt = template.system_template.format(**{k: variables[k] for k in system_required})
        user_prompt = template.user_template.format(**{k: variables[k] for k in user_required})
        return system_prompt, user_prompt

    @staticmethod
    def _required_fields(template: str) -> set[str]:
        return {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}


def serialize_untrusted_block(content: Any) -> str:
    """Serialize untrusted content into a safe, explicit JSON block for prompts."""
    return json.dumps(content, ensure_ascii=False, sort_keys=True)


def build_default_prompt_registry() -> PromptRegistry:
    return PromptRegistry(
        templates=[
            PromptTemplate(
                name="agent_generate_json",
                version="v1",
                system_template="Task: {task_type}. Return valid JSON only.",
                user_template="{payload_json}",
            ),
            PromptTemplate(
                name="agent_repair_json",
                version="v1",
                system_template="Repair the following content into valid JSON only. Return JSON with no markdown.",
                user_template="Return strict JSON only for this task payload.\\n{payload_json}\\nPrevious invalid output:\\n{invalid_output_json}",
            ),
            PromptTemplate(
                name="niche_intelligence_analyze",
                version="v1",
                system_template=(
                    "You are Niche Intelligence Analyst. Return strict JSON only. "
                    "Do not include markdown. Avoid guaranteed revenue claims. "
                    "Evaluate originality potential, production difficulty, compliance risk, and differentiation opportunities. "
                    "Scores must be 0-100. Required keys: summary, score_explanations, strengths, weaknesses, risks, recommended_positioning, content_pillar_suggestions, differentiation_opportunities, compliance_notes, next_actions, scores."
                ),
                user_template="Analyze this channel context and notes:\n{payload_json}",
            ),
            PromptTemplate(
                name="topic_research_analyze",
                version="v1",
                system_template=(
                    "You are a topic research analyst. Return strict JSON only with no markdown. "
                    "Allowed recommendation values: pursue, refine, reject. "
                    "Required JSON shape: {\"recommendation\": string, \"rationale\": string, \"key_points\": string[], \"scores\": {\"demand_score\":0-100,\"competition_score\":0-100,\"novelty_score\":0-100,\"channel_fit_score\":0-100,\"execution_risk_score\":0-100,\"overall_score\":0-100}}."
                ),
                user_template="Analyze this topic idea against channel context and memory:\n{payload_json}",
            ),
        ]
    )
