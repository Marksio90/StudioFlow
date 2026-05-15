# Angle Generation Prompt

Template: `angle_generate@v2`

## Objective
Generate high-signal, non-generic content angles that are strategically differentiated for the specific channel context.

## Hard Behavioral Constraints
- Return strict JSON only (no markdown, no prose wrapper).
- Output must satisfy the exact schema and field requirements below.
- Do not output generic advice or interchangeable “viral” framing.
- Do not fabricate certainty where the provided context is weak.

## Anti-Generic Requirements (Mandatory)
Every proposed angle must:
- Include at least one explicit **differentiator** that is specific, testable, and non-boilerplate.
- Include a **human_judgment_required** rationale describing what editorial judgment is needed and why automation alone is insufficient.
- Be traceable to input evidence; avoid unsupported assumptions.

Reject weak angle construction patterns:
- Commodity framing that could apply to any channel.
- Vague hooks (e.g., “this changes everything”) without concrete audience tension.
- Redundant ideas that mirror known channel memory without novelty.

## Refusal Rules (Low-Evidence / Generic Inputs)
If context is insufficient to safely generate differentiated angles, refuse generation.

Use refusal when one or more are true:
- Missing core channel context or audience intent.
- Candidate direction is too generic to produce unique angles.
- Evidence density is too low to justify specific claims.

In refusal mode, still return valid JSON matching the same top-level schema with:
- `status = "refused"`
- zero-length `angles`
- clear `refusal.reason_codes`
- concrete `refusal.next_inputs_needed`

## Output Schema (Strict)
- Top-level object keys are required: `status`, `angles`, `refusal`.
- `status` enum: `"ok" | "refused"`
- `angles` must be an array (present even if empty).
- `refusal` must always be present.

### Required JSON Shape
```json
{
  "status": "ok",
  "angles": [
    {
      "headline": "string",
      "hook": "string",
      "summary": "string",
      "audience": "string",
      "differentiator": "string",
      "human_judgment_required": "string",
      "evidence_basis": ["string"],
      "scores": {
        "novelty": 0,
        "specificity": 0,
        "audience_fit": 0,
        "evidence_strength": 0,
        "overall": 0
      }
    }
  ],
  "refusal": {
    "reason_codes": [],
    "message": "",
    "next_inputs_needed": []
  }
}
```

### Score Constraints
All score fields are required integers in range `0-100`.

### Additional Contract Rules
- If `status = "ok"`: `angles.length >= 1` and `refusal.reason_codes` should be empty.
- If `status = "refused"`: `angles.length = 0` and `refusal.reason_codes.length >= 1`.
- Keep arrays present even when empty.
