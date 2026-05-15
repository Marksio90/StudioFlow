# Content Idea Board

## Purpose: Pre-Generation Operational Center

The **Content Idea Board** is the operational hub where content opportunities are captured, organized, and prepared *before* any generation work begins.

Its primary purpose is to:

- Centralize all candidate ideas in one auditable workspace.
- Establish editorial intent (topic, audience, angle, format, priority) before production execution.
- Make handoff into downstream stages predictable by ensuring every idea has required metadata and clear ownership.
- Provide transparent queue visibility for planning, capacity management, and cross-functional coordination.

This stage is intentionally operational, not creative automation. It ensures the pipeline starts from structured, validated inputs.

## Status Definitions and Expected Progression

Statuses represent workflow readiness, not quality scoring.

- **Backlog**
  - Idea is captured but not yet reviewed.
  - May be incomplete or unprioritized.

- **Ready for Brief**
  - Idea has minimum required fields and is approved to move forward.
  - Ready for conversion into a formal content brief.

- **Deferred**
  - Idea is intentionally paused (timing, dependency, capacity, or strategy reasons).
  - Kept for future reactivation rather than discarded.

- **Archived**
  - Idea is closed and not expected to progress.
  - Useful for historical traceability and avoiding duplicate re-submission.

### Expected Progression

Normal forward flow:

`Backlog -> Ready for Brief -> (handoff to brief/generation pipeline)`

Alternative outcomes:

- `Backlog -> Deferred -> Backlog/Ready for Brief` (when reactivated)
- `Backlog or Deferred -> Archived` (when retired)

This progression keeps state transitions explicit and operationally deterministic.

## Fit Within the Full Production Pipeline

The Content Idea Board is the **first controlled stage** in the end-to-end production lifecycle:

1. **Idea Intake & Triage (this board)**
2. Brief Authoring
3. Content Generation / Draft Creation
4. Editorial Review
5. Compliance / Brand / QA Checks
6. Scheduling & Distribution
7. Publishing
8. Performance Monitoring & Iteration

The board ensures only operationally ready ideas enter Brief Authoring, reducing rework and downstream bottlenecks.

## Why Ideas Do Not Go Directly to Publishing

Ideas are high-level intents, not publishable assets. Direct publishing is prevented because:

- Ideas lack required production artifacts (full draft, approved messaging, assets, metadata, links, legal checks).
- Editorial and compliance controls must occur before public release.
- Skipping intermediate stages creates quality, brand, and governance risk.
- Production sequencing (brief -> draft -> review -> schedule) is required for consistency and accountability.

The board exists to improve throughput and quality by enforcing structured readiness—not to bypass the production lifecycle.

## Deterministic CRUD Scope for This Phase

This phase is strictly **deterministic CRUD** over idea records.

### In Scope

- **Create** ideas with required and optional fields.
- **Read** ideas and filters by status, owner, channel, campaign, and date.
- **Update** idea fields and status transitions according to allowed workflow rules.
- **Delete/Archive** ideas per retention policy (hard delete only where explicitly permitted).

### Out of Scope

- AI ranking, scoring, or autonomous prioritization.
- Generative writing, draft synthesis, or tone optimization.
- Predictive performance modeling.

Any intelligence-based decisioning belongs to later stages or separate services. The Content Idea Board remains deterministic to keep behavior explainable, testable, and operationally reliable.
