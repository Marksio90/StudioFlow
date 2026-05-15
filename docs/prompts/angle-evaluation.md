# Angle Evaluation Prompt

Template: `angle_evaluate@v2`

## Objective
Evaluate proposed angles using strict, evidence-aware criteria and produce machine-parseable decisions with explicit rejection behavior for low-evidence or generic proposals.

## Hard Behavioral Constraints
- Return strict JSON only (no markdown, no prose wrapper).
- Output must match required schema exactly.
- No generic rationales; each decision must include concrete diagnostics.

## Mandatory Human-Judgment + Differentiator Checks
For each candidate angle, the evaluator must explicitly assess:
- Whether the angle contains a meaningful and testable differentiator.
- Whether the proposed execution requires material human editorial judgment.

If either is missing or weak, downgrade recommendation and explain why.

## Refusal/Reject Conditions
Mark a candidate `reject` when any apply:
- Evidence is too weak to support core claims.
- Framing is generic or near-duplicate of known channel patterns.
- No clear audience tension or channel-fit mechanism.

If all candidates fail evidence threshold, set top-level `status = "refused"`.

## Output Schema (Strict)
Top-level required keys: `status`, `evaluations`, `refusal`.
- `status` enum: `"ok" | "refused"`
- `evaluations` must be present as array.
- `refusal` must be present.

### Required JSON Shape
```json
{
  "status": "ok",
  "evaluations": [
    {
      "angle_index": 0,
      "recommendation": "approve",
      "rationale": "string",
      "differentiator_assessment": "string",
      "human_judgment_assessment": "string",
      "evidence_gaps": ["string"],
      "scores": {
        "hook_clarity": 0,
        "novelty": 0,
        "audience_fit": 0,
        "differentiation_strength": 0,
        "human_judgment_depth": 0,
        "evidence_strength": 0,
        "risk": 0,
        "overall_score": 0
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

### Field Constraints
- `angle_index` is required integer.
- `recommendation` enum: `"approve" | "refine" | "reject"`.
- Every score is a required integer in range `0-100`.

### Status Coupling Rules
- If `status = "ok"`: at least one evaluation should be present.
- If `status = "refused"`: `evaluations` may be empty and `refusal.reason_codes.length >= 1`.
