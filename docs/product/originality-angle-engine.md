# Originality Angle Engine

## Purpose: anti-generic quality gate

The Originality Angle Engine is a deterministic quality gate that prevents generic, interchangeable, or low-novelty content concepts from moving forward in the production pipeline.

It exists to ensure each approved concept has a **clear differentiator** (the "angle") rather than merely rephrasing common advice. The engine acts as a hard checkpoint between ideation and downstream drafting/generation so operators do not need to manually police originality on every item.

Core goals:

- Block concepts that are broadly true but not specifically ownable.
- Increase repeatable novelty across a batch, not just one-off creative wins.
- Preserve editorial trust by making acceptance criteria explicit and auditable.
- Reduce subjective drift by converting originality standards into deterministic rules.

## Required angle field definitions

Each candidate concept must provide the following required angle payload. Missing required fields make the candidate ineligible for approval.

- `angle_hook` *(string, required)*: A one-sentence statement of the unique framing. Must describe **what is different** versus default category advice.
- `angle_mechanism` *(string, required)*: The causal logic for why the angle works. Should describe the mechanism, not just the outcome.
- `angle_audience` *(string, required)*: The specific audience segment the angle is for (experience level, context, constraints).
- `angle_context` *(string, required)*: The situational boundary where this angle is valid (platform, market condition, time horizon, format, etc.).
- `angle_contrast_baseline` *(string, required)*: The “generic baseline” this angle is contrasted against.
- `angle_evidence_mode` *(enum, required)*: Expected support type for downstream substantiation. Allowed values:
  - `empirical`
  - `expert_pattern`
  - `comparative_example`
  - `first_principles`
- `angle_risks` *(string[], required)*: Known failure modes, caveats, or misuse risks.
- `originality_score` *(number, required)*: Normalized score from 0.00 to 1.00 produced by the evaluator.
- `specificity_score` *(number, required)*: Normalized score from 0.00 to 1.00 reflecting concreteness.
- `clarity_score` *(number, required)*: Normalized score from 0.00 to 1.00 reflecting unambiguous phrasing.
- `genericity_flags` *(string[], required)*: Deterministic flags indicating detected generic patterns (empty array when none).

## Scoring interpretation

Scores are interpreted as bounded quality signals and are not free-form opinions.

- `originality_score`
  - `0.00 - 0.39`: Generic or derivative; insufficient novelty.
  - `0.40 - 0.64`: Some differentiation, but still likely interchangeable.
  - `0.65 - 0.79`: Meaningfully differentiated and likely worth advancing.
  - `0.80 - 1.00`: Strong novelty with clearly ownable framing.

- `specificity_score`
  - `0.00 - 0.49`: Vague framing; missing concrete boundaries.
  - `0.50 - 0.74`: Partially concrete; may need tightening.
  - `0.75 - 1.00`: Actionable and operationally precise.

- `clarity_score`
  - `0.00 - 0.49`: Ambiguous or overloaded wording.
  - `0.50 - 0.74`: Understandable but open to interpretation.
  - `0.75 - 1.00`: Clear, crisp, and interpretation-stable.

Interpretation principle:

- A high originality score does **not** compensate for poor specificity or clarity.
- Composite decisions are gate-rule-driven (see below), not manually averaged in the UI.

## Deterministic approval gate rules and override policy

Approval is determined by deterministic rules executed in order.

### Rule order

1. **Schema validation gate**
   - Reject if any required field is missing or malformed.
2. **Genericity hard-fail gate**
   - Reject if `genericity_flags` contains any hard-fail class (e.g., empty-claim pattern, cliché framing, universal advice with no boundary).
3. **Score threshold gate**
   - Reject unless all conditions are true:
     - `originality_score >= 0.70`
     - `specificity_score >= 0.70`
     - `clarity_score >= 0.70`
4. **Risk disclosure gate**
   - Reject if `angle_risks` is empty.
5. **Approve**
   - Approve automatically when all prior gates pass.

### Override policy

Overrides are exceptional and explicit.

- Only users with override capability may override a rejection.
- Override requires:
  - `override_reason_code` (enum), and
  - `override_rationale` (free text), and
  - operator identity and timestamp.
- Overrides are allowed only for these reason codes:
  - `time_critical_publish`
  - `strategic_experiment`
  - `known_false_positive`
- Overrides do **not** mutate underlying scores or flags; they only alter disposition.
- All overrides must be auditable and queryable by candidate id, operator id, and date range.

## API contract summary

The engine exposes a stable request/response contract at a high level.

### Evaluate request

- Method: `POST`
- Path: `/api/originality-angle/evaluate`
- Body:
  - Candidate content metadata (id, workspace/project, source prompt lineage)
  - Required angle fields (see definitions)

### Evaluate response

- `decision`: `approved | rejected`
- `rejection_reasons`: string[] (empty when approved)
- `scores`:
  - `originality_score`
  - `specificity_score`
  - `clarity_score`
- `genericity_flags`: string[]
- `rule_trace`: ordered list of evaluated rules and outcomes
- `evaluation_id`: immutable id for traceability
- `evaluated_at`: ISO-8601 timestamp

### Override endpoint

- Method: `POST`
- Path: `/api/originality-angle/overrides`
- Body:
  - `evaluation_id`
  - `override_reason_code`
  - `override_rationale`
- Response:
  - final disposition
  - override metadata (operator, timestamp)

## Operator workflow in UI

1. Operator submits or selects a concept candidate.
2. UI validates required fields client-side for completeness.
3. Operator runs “Evaluate originality angle”.
4. UI displays decision banner:
   - Approved: proceed to next pipeline stage.
   - Rejected: show deterministic rejection reasons, score breakdown, and rule trace.
5. If rejected and operator has permission, UI offers “Request/Apply override”.
6. Override modal requires reason code + rationale before submission.
7. UI writes resulting disposition, then updates activity timeline/audit panel.

Operator UX requirements:

- No silent auto-corrections to submitted angle text.
- Rejection reasons must map 1:1 to gate rules.
- Rule trace must be visible (collapsible is acceptable).
- Override affordance must be permission-gated and visually distinct from normal approval.

## Observability and audit expectations

Every evaluation and disposition event must be observable and auditable end-to-end.

### `LLMCall` expectations

When an LLM-assisted evaluator contributes to scoring/flags, persist an `LLMCall` record with:

- `llm_call_id`
- model identifier/version
- prompt template/version
- input payload hash
- output payload hash
- token usage (prompt/completion/total)
- latency and error status
- correlation ids linking to `evaluation_id` and candidate id

### Approval records

For non-overridden approvals, persist:

- `evaluation_id`
- final `decision=approved`
- full score vector
- genericity flags
- rule trace
- operator (if human-triggered)
- timestamps

### Override records

For overrides, persist an immutable override event containing:

- prior decision and reasons
- override decision
- `override_reason_code`
- `override_rationale`
- overriding operator identity
- timestamp
- linked `evaluation_id`

### Auditability standards

- All decision-affecting events are append-only.
- Every final disposition is reconstructable from event history.
- It must be possible to answer: who approved, who overrode, why, and based on what evidence.
- Monitoring should expose override rate, false-positive override patterns, and rule-level reject distribution.
