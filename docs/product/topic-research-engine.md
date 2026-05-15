# Topic Research Engine (MVP)

## 1) Scope and Non-Goals

### Scope
The Topic Research Engine (TRE) provides **structured, LLM-assisted topic recommendations** for product users based on:
- a user-provided prompt or content seed,
- recently analyzed topics,
- historical analysis records,
- internally available metadata and configured rules.

For MVP, TRE is responsible for:
- generating candidate topics,
- scoring candidates against required product-defined criteria,
- ranking and returning recommendations,
- exposing three backend entry points (`analyze`, `latest`, `history`),
- supporting a deterministic frontend state model for loading, success, empty, and error states,
- recording LLM call telemetry for debugging and quality monitoring.

### Non-Goals (MVP)
TRE MVP explicitly does **not** include:
- autonomous web browsing,
- direct calls to unconfigured third-party APIs,
- real-time trend mining from the public internet,
- agentic multi-step research workflows with tool use beyond preconfigured internal sources,
- full explainability graphs beyond compact recommendation rationale.

---

## 2) Required Scores and Recommendation Definitions

### Recommendation Object (Canonical)
Each recommendation must include:
- `topic_id` (stable ID within result set or persisted record),
- `title` (human-readable topic name),
- `summary` (1–3 sentence rationale),
- `scores` (required score bundle; see below),
- `composite_score` (final normalized rank score),
- `confidence` (`low` | `medium` | `high`),
- `reasons` (short bullet-like textual evidence),
- `created_at` (UTC timestamp),
- `version` (scoring/ranking version tag for reproducibility).

### Required Score Dimensions
All recommendations must contain these normalized score dimensions (`0.0` to `1.0`):
1. **Relevance**: alignment to user intent, prompt, and context.
2. **Impact**: potential user/business value if topic is pursued.
3. **Feasibility**: practical achievability within known constraints.
4. **Novelty**: differentiation from already-covered recent topics.
5. **Evidence Quality**: quality and sufficiency of internal evidence used.

### Composite Score
- `composite_score` is computed from a weighted combination of required dimensions.
- Weights must be centrally configured (not hardcoded per request).
- If a dimension is unavailable, the engine must either:
  - compute with documented fallback weighting, or
  - reject recommendation generation with a validation error (preferred when data quality is too low).

### Recommendation Tiers (Definition)
For consistent UI and downstream logic, classify by `composite_score`:
- **Strong Recommend**: `>= 0.80`
- **Recommend**: `>= 0.65` and `< 0.80`
- **Consider**: `>= 0.50` and `< 0.65`
- **Do Not Recommend (filtered)**: `< 0.50` (normally hidden unless debug mode)

Thresholds are product-configurable but must remain explicit and versioned.

---

## 3) Backend Flow (`analyze`, `latest`, `history`)

### 3.1 `analyze`
`analyze` is the primary execution path.

**Input (minimum):**
- `query` or structured seed content,
- optional context (audience, domain, constraints),
- optional request metadata (session/user IDs, trace IDs).

**Flow:**
1. Validate input shape and required fields.
2. Load configuration (weights, thresholds, feature flags).
3. Gather internal context sources (allowed/preconfigured only).
4. Build prompt package and call LLM for candidate generation.
5. Score each candidate across required dimensions.
6. Compute `composite_score`, tier, and confidence.
7. Sort/rank and apply filtering rules.
8. Persist run artifact (request, response, metadata, timing).
9. Return ranked recommendations + execution metadata.

**Output:**
- ranked recommendation list,
- summary statistics (count, score ranges),
- run identifiers for traceability.

### 3.2 `latest`
`latest` returns the most recent successful analysis result for a scope.

**Purpose:**
- fast reload of latest recommendations without recomputation,
- UI hydration for recent sessions.

**Behavior:**
- fetch most recent successful run by user/team/project scope,
- return stored recommendations and metadata,
- return `empty` if no previous successful run exists.

### 3.3 `history`
`history` returns past analyses for audit and UX recall.

**Behavior:**
- list prior runs in reverse chronological order,
- include minimal metadata per run (run ID, created time, query snippet, status, top score),
- support pagination/cursor,
- optionally return detailed record on drill-down.

---

## 4) Frontend Behavior and State Model

### Core UX Behavior
Frontend must support three user intents:
1. submit a new analysis (`analyze`),
2. reopen the most recent result (`latest`),
3. review earlier runs (`history`).

### State Model
Use an explicit, finite state model:
- `idle` — initial state, no active request,
- `loading.analyze` — analyze request in flight,
- `loading.latest` — latest request in flight,
- `loading.history` — history request in flight,
- `success.withData` — successful response with recommendations,
- `success.empty` — successful response with no data,
- `error.validation` — user/input validation errors,
- `error.execution` — backend/LLM/runtime failures,
- `error.network` — transport-level failures.

### State Transitions (High-Level)
- `idle -> loading.analyze -> success.withData | success.empty | error.*`
- `idle -> loading.latest -> success.withData | success.empty | error.*`
- `idle -> loading.history -> success.withData | success.empty | error.*`

### UI Requirements
- disable duplicate submissions while `loading.analyze`,
- preserve last successful payload for non-destructive error handling,
- show tier badges and per-dimension scores,
- show deterministic empty-state copy when no recommendations/history exist,
- expose run ID in UI for support/debug.

---

## 5) Observability (LLMCall Logging)

### Logging Standard
Each LLM interaction must emit a structured `LLMCall` event/log entry.

### Required `LLMCall` Fields
- `timestamp_utc`,
- `trace_id` / `request_id` / `run_id`,
- `operation` (`analyze.generateCandidates`, `analyze.score`, etc.),
- `model` and model version,
- prompt template/version identifiers,
- token usage (prompt, completion, total),
- latency (ms),
- outcome (`success` | `error`),
- error class/code/message (if failed),
- safe prompt/response hashes or redacted snapshots per privacy policy.

### Observability Outcomes
MVP logs must support:
- reproducibility of recommendation runs,
- latency and cost monitoring,
- error triage by operation and model,
- post-hoc quality analysis tied to score outputs.

---

## 6) Validation and Error Handling Standards

### Validation Standards
At minimum, validate:
- required fields present and non-empty,
- string lengths and payload size limits,
- enum/domain correctness for known fields,
- score range guarantees (`0.0–1.0`),
- output schema integrity before returning to client.

### Error Contract
All API errors should return a normalized envelope:
- `error.code` (stable machine-readable code),
- `error.type` (`validation`, `execution`, `dependency`, `rate_limit`, `unknown`),
- `error.message` (safe user-facing summary),
- `error.details` (optional structured diagnostics),
- `trace_id` (for support correlation).

### Handling Rules
- validation failures: fail fast, no LLM call,
- transient dependency failures: retry with bounded policy,
- unrecoverable LLM/runtime failures: return execution error and persist failure record,
- never return partial malformed recommendations; either return valid schema or explicit error.

---

## 7) MVP Limitations

To keep MVP predictable, safe, and auditable:

1. **No autonomous web browsing.**
   The engine must not browse arbitrary websites during analysis.

2. **No external API calls unless explicitly preconfigured.**
   Only approved/internal connectors and preconfigured integrations are allowed.

3. **No dynamic tool discovery at runtime.**
   Available tools/sources are static per deployment configuration.

4. **No unbounded agent loops.**
   Analysis execution must be single-pass or bounded multi-step within strict limits.

5. **No guarantee of objective truth.**
   Recommendations are probabilistic outputs; confidence and evidence quality must be surfaced.

These constraints may be relaxed in future versions after security, reliability, and governance controls are expanded.
