# Topic Research Prompt

Template: `topic_research_analyze@v1`

## Objective
Produce a **research-grade topic analysis plan** for a single content idea before any scripting work begins. The output must:
- Stress-test the idea’s strategic potential for the target channel.
- Identify where the idea is weak, generic, or unsupported.
- Extract concrete evidence requirements needed to validate claims later.
- Return strict machine-parseable JSON that matches the backend Pydantic contract.

## Input Contract
Inputs are required unless marked optional.

1. **ContentIdea** (required)
   - Canonical candidate idea object from backend.
   - Includes the working title/topic, audience intent, and any known claim angles.

2. **ChannelMemory** (required)
   - Historical channel context used to avoid repetition.
   - Includes prior topics covered, recurring formats, known audience preferences, and performance patterns.

3. **Manual Notes** (optional, but must be consumed if present)
   - Freeform operator notes (e.g., sponsor constraints, editorial priorities, excluded angles, newly observed trends).
   - Treat these as higher-priority context when they conflict with default heuristics.

If required inputs are missing or malformed, return valid JSON with `status = "needs_input"` and enumerate missing fields.

## Anti-Generic Guidance
Do not produce boilerplate advice. Flag and penalize genericity using concrete mechanisms:
- Compare against ChannelMemory-covered themes and reject near-duplicates unless a clear novelty vector exists.
- Avoid vague recommendations like “make it more engaging” without specifying *what exactly* is missing.
- Prefer testable differentiators (unique framing, uncommon evidence source, specific audience pain point).
- Require explicit rationale for why this topic is timely *for this channel*, not just broadly popular.

## Weak-Idea Detection Rules
Mark an idea as weak when one or more of the following hold:
- **Commodity framing**: The angle is already saturated and indistinguishable from common creator output.
- **No audience tension**: There is no clear problem, contradiction, curiosity gap, or outcome urgency.
- **Evidence fragility**: Core claims depend on anecdotes, unclear stats, or unverifiable assumptions.
- **Format mismatch**: The topic is poorly aligned with channel format strengths captured in ChannelMemory.
- **Low differentiation path**: No realistic way to create a distinct perspective without excessive speculation.

Each triggered weak-idea rule must include:
- `rule_id`
- short plain-language explanation
- severity (`low|medium|high`)
- remediation note (or `null` if not recoverable)

## Evidence Requirement Extraction Rules
Extract a structured list of evidence requirements to be satisfied in downstream research/script phases:
- Convert each major claim or implication into a verification task.
- Label requirement type (e.g., `statistic`, `historical_fact`, `expert_opinion`, `case_study`, `counterpoint`).
- Specify minimum source quality threshold (primary source preferred; otherwise high-credibility secondary).
- Include freshness constraints when recency matters.
- Add “disconfirming evidence” requirements for claims likely to be overstated.

Do **not** fabricate sources in this phase. Only define what evidence is needed.

## Hard Constraint: No Script Generation in This Phase
This phase is strictly for topic research planning. Do not output:
- script lines
- scene/shot narration
- hooks/outros copy
- final talking points written as production script

Any script-like output is a contract violation.

## Output Requirements
- Return strict JSON only (no markdown, no prose wrapper).
- Include every required field.
- Use backend enum values exactly.
- Keep arrays present even when empty.

### JSON Schema Example (Pydantic-Compatible)
```json
{
  "status": "ok",
  "summary": {
    "thesis": "This topic has moderate upside if narrowed to a specific audience pain point.",
    "decision": "revise",
    "confidence": 0.78
  },
  "genericity": {
    "is_generic": true,
    "score": 71,
    "reasons": [
      "Angle overlaps with three recently covered channel topics",
      "Current framing lacks a concrete novelty vector"
    ]
  },
  "weak_idea_signals": [
    {
      "rule_id": "commodity_framing",
      "severity": "high",
      "explanation": "Topic framing mirrors common creator playbooks without a distinct mechanism.",
      "remediation": "Constrain scope to one contrarian claim and validate against channel-specific outcomes."
    },
    {
      "rule_id": "evidence_fragility",
      "severity": "medium",
      "explanation": "Primary supporting claim appears anecdotal and currently unverified.",
      "remediation": "Require at least one primary dataset and one independent corroborating source."
    }
  ],
  "evidence_requirements": [
    {
      "claim_id": "claim_1",
      "requirement_type": "statistic",
      "question": "What recent quantitative evidence supports the stated trend?",
      "minimum_source_quality": "primary_or_official",
      "freshness": "<=12_months",
      "disconfirming_required": true
    },
    {
      "claim_id": "claim_2",
      "requirement_type": "counterpoint",
      "question": "What credible evidence contradicts the main assumption?",
      "minimum_source_quality": "high_credibility_secondary",
      "freshness": "best_available",
      "disconfirming_required": true
    }
  ],
  "novelty_paths": [
    {
      "label": "audience-segment reframing",
      "description": "Reframe around a specific operator persona with measurable constraints.",
      "estimated_lift": "medium"
    }
  ],
  "missing_inputs": [],
  "notes": []
}
```

If inputs are insufficient, emit the same schema with `status = "needs_input"` and populate `missing_inputs`.
