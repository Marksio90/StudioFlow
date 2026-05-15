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
                name="angle_generate",
                version="v2",
                system_template=(
                    "You generate differentiated YouTube content angles. Return strict JSON only with no markdown. "
                    "Enforce anti-generic constraints: each angle must include a concrete differentiator and a human_judgment_required explanation. "
                    "If context is low-evidence or too generic, refuse with status=refused and empty angles. "
                    "Required top-level keys: status, angles, refusal. "
                    "Required angle keys: headline, hook, summary, audience, differentiator, human_judgment_required, evidence_basis, scores. "
                    "Score keys novelty,specificity,audience_fit,evidence_strength,overall must be integers 0-100."
                ),
                user_template="Generate angle candidates using this context:\n{payload_json}",
            ),
            PromptTemplate(
                name="angle_generate",
                version="v1",
                system_template=(
                    "You generate YouTube content angles. Return strict JSON only with no markdown. "
                    "Return exactly the requested number of angles in this shape: "
                    '{"angles":[{"headline":string,"hook":string,"summary":string,"audience":string}]}.'
                ),
                user_template="Generate angle candidates using this context:\n{payload_json}",
            ),
            PromptTemplate(
                name="angle_evaluate",
                version="v2",
                system_template=(
                    "You evaluate proposed content angles with strict evidence and differentiation criteria. "
                    "Return strict JSON only with no markdown. "
                    "Required top-level keys: status, evaluations, refusal. "
                    "For each evaluation require: angle_index, recommendation, rationale, differentiator_assessment, human_judgment_assessment, evidence_gaps, scores. "
                    "recommendation must be approve|refine|reject. "
                    "Score keys hook_clarity, novelty, audience_fit, differentiation_strength, human_judgment_depth, evidence_strength, risk, overall_score must be integers 0-100. "
                    "Reject low-evidence or generic proposals; if all fail set status=refused with refusal reasons."
                ),
                user_template="Evaluate these candidates with full context:\n{payload_json}",
            ),
            PromptTemplate(
                name="angle_evaluate",
                version="v1",
                system_template=(
                    "You evaluate proposed content angles. Return strict JSON only with no markdown. "
                    "Return one evaluation per candidate in this shape: "
                    '{"evaluations":[{"angle_index":int,"scores":{"hook_clarity":0..1,"novelty":0..1,"audience_fit":0..1,"risk":0..1,"overall_score":0..1},"recommendation":"approve|refine|reject","rationale":string}]}.'
                ),
                user_template="Evaluate these candidates with full context:\n{payload_json}",
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
