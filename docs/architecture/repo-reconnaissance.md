# Repository Reconnaissance — QualityTube OS Transition

## 1) Current repository structure
- `apps/backend` — FastAPI service, SQLAlchemy models, Alembic migrations, domain services, repository layer, pytest suite.
- `apps/frontend` — Next.js (pages router) UI, API client adapter to backend OpenAPI types.
- `apps/worker` — Celery worker with async task wrappers for publish/analytics operations.
- `packages/shared` — generated OpenAPI TypeScript contracts (`src/backend-api.ts`, `openapi/backend.openapi.json`).
- `infra` — helper scripts (`wait-for-it.sh`).
- `.github/workflows/ci.yml` — CI pipeline.
- `docker-compose.yml` — local multi-service orchestration (frontend, backend, worker, postgres, redis).

## 2) Current product narrative
- `README.md` defines “AI Media Operations OS” for YouTube creators/teams/agencies, explicitly not spam automation.
- Narrative already aligns partially with QualityTube OS philosophy: planning, quality, compliance, approvals, analytics, quota/cost control.
- Foundation-stage disclaimers exist: frontend mock tendencies, backend persistence hardening in progress, worker placeholders.

## 3) Current backend architecture
- Entrypoint: `apps/backend/app/main.py` (FastAPI, `/health`, CORS allowlist, in-process rate limiter middleware).
- API modules:
  - `apps/backend/app/api/video_projects.py`
  - `apps/backend/app/api/usage.py`
  - deps/errors in `apps/backend/app/api/deps.py`, `errors.py`.
- Services (application layer):
  - `video_project_service.py` (orchestration facade)
  - `workflow_engine.py` (workflow state/events)
  - `compliance_service.py`, `analytics_service.py`, `youtube_quota_service.py`, `usage_service.py`, `plan_limit_service.py`
  - `product_agents.py` (mock/tracked LLM agents)
  - `model_router.py` (task→model env routing)
- Repository layer: `app/repositories/video_project_repository.py` with both `InMemoryVideoProjectRepository` and `DBVideoProjectRepository`.
- Persistence: SQLAlchemy models in `app/db/models.py`; async session in `app/db/session.py`; migrations under `alembic/versions/*`.

## 4) Current frontend architecture
- Next.js pages router (`apps/frontend/pages/*`):
  - index, project list/detail/create, compliance detail.
- Shared layout/component: `components/Layout.tsx`.
- Typed API client:
  - `lib/apiClient.ts` maps backend DTOs to frontend `lib/types.ts` domain shapes.
  - Uses generated contract types from `packages/shared/src/backend-api.ts`.
- Important mismatch risk: client sends `decision_note` in approval payload, while backend `ApprovalDecisionIn` appears to expect `comment`/`decided_by_user_id` (verify via `apps/backend/app/schemas/video_project.py`).

## 5) Current worker/Celery architecture
- Celery app config: `apps/worker/worker_app.py` (Redis broker/backend).
- Tasks: `apps/worker/app/tasks/video_workflow.py`
  - `workflow.video.start` (stub queued response)
  - `workflow.video.publish` and `workflow.video.sync_analytics` use async DB repo + retry/backoff.
- Tracks idempotency via `TaskExecution`/`TaskAttempt` repository calls.
- Observability hooks through `app.observability` trace/metrics.

## 6) Current AI/LLM provider architecture
- Implemented in `apps/backend/app/services/product_agents.py`:
  - `TrackedLLMClient`, `MockLLMProvider`, `CostTracker` protocol + noop tracker.
  - Agent classes: `ResearchAgent`, `ScriptAgent`, `SEOAgent`, `ComplianceAgent`, `PerformanceAgent`-style outputs (file continues beyond excerpt).
- `ModelRouter` (`model_router.py`) maps task types to env vars like `LLM_SCRIPT_MODEL` with fallback `LLM_DEFAULT_MODEL`.
- Provider is mock/deterministic currently (`provider="mock-openai"` recorded in cost events).

## 7) Current YouTube integration architecture
- No direct YouTube OAuth flow endpoints/controllers found.
- YouTube integration currently represented by:
  - Quota ledger service `youtube_quota_service.py`
  - Publishing state transitions in `VideoProjectService.publish_video()` generating synthetic `youtube_video_id` (`yt_<id>`)
  - Worker publish task calling service methods.
- Conclusion: operational scaffolding exists, real API/OAuth integration does not yet exist.

## 8) Current database/domain model map
Defined in `apps/backend/app/db/models.py`:
- Tenant/core: `Organization`, `Workspace`, `User`, `Membership`, `Channel`.
- Content lifecycle: `VideoProject`, `VideoIdea`, `ScriptDraft`, `SEORecommendation`, `ComplianceReport`.
- Workflow: `WorkflowRun`, `WorkflowStep`, `WorkflowEvent`, `TaskExecution`, `TaskAttempt`.
- Governance/cost: `ApprovalDecision`, `LLMCall`, `LLMCostLedgerEntry`, `YouTubeQuotaLedgerEntry`.
- Delivery/analytics/media: `PublishingPlan`, `AnalyticsSnapshot`, `Asset`, `AssetLicense`.

## 9) Current API route map
From `app/api/video_projects.py` and `app/api/usage.py`:
- `/health`
- `/api/v1/video-projects` (GET, POST)
- `/api/v1/video-projects/{project_id}` (GET, PATCH, DELETE)
- `/api/v1/video-projects/{project_id}/start-workflow`
- `/request-approval`, `/approve`, `/reject`, `/needs-changes`
- `/approval-decisions`, `/events`, `/costs`, `/quota`
- `/compliance` (GET, POST)
- `/analytics` (GET, POST)
- `/api/v1/video-projects/publishing-plans` (POST)
- `/api/v1/video-projects/publishing-plans/{plan_id}/schedule` (POST)
- `/api/v1/video-projects/publishing-plans/{plan_id}/publish` (POST)
- `/api/v1/usage/{organization_id}` (GET)
- `/api/v1/usage/{organization_id}/channels/{channel_id}` (POST)

## 10) Current shared contracts/types map
- OpenAPI artifact: `packages/shared/openapi/backend.openapi.json`.
- Generated TS types: `packages/shared/src/backend-api.ts`.
- Frontend consumes these in `apps/frontend/lib/apiClient.ts` and verifies via `apiClient.contract.test.ts`.

## 11) Current docs map
- `README.md` only substantial root-level documentation found in inspected files.
- No pre-existing `docs/` tree was present before this report creation.

## 12) Current Docker/infra/CI setup
- `docker-compose.yml`: postgres16, redis7, backend, worker, frontend; healthchecks on backend/worker/db/redis.
- Dockerfiles per app:
  - `apps/backend/Dockerfile`
  - `apps/frontend/Dockerfile`
  - `apps/worker/Dockerfile`
- CI: `.github/workflows/ci.yml`
  - backend lint/typecheck (`ruff`, `mypy`)
  - backend tests with 80% coverage gate
  - frontend typecheck/lint
  - security (`pip-audit`, `npm audit`)
  - FE/BE contract check
  - docker compose build

## 13) Current test coverage summary
Backend pytest modules include:
- `test_video_project_api.py`, `test_models.py`, `test_concurrent_video_project_pipeline.py`
- `test_compliance_service.py`, `test_repetitive_content_detector.py`
- `test_model_router.py`, `test_product_agents.py`
- `test_youtube_quota_service.py`, `test_usage_limits.py`, `test_system_invariants.py`
Frontend:
- `lib/apiClient.contract.test.ts` contract-focused check.
CI enforces backend 80% minimum coverage, but this reconnaissance did not execute tests.

## 14) Existing modules by requested domain
- channels: DB model `Channel`; usage registration endpoints/service.
- topics: no first-class Topic entity found (likely implicit in project metadata/frontend fields).
- content ideas: DB model `VideoIdea` exists, but no dedicated API exposed in inspected routes.
- scripts: DB model `ScriptDraft`; script generation logic in `product_agents.py`.
- briefs: no explicit `Brief` model/module found.
- publishing: `PublishingPlan` model + schedule/publish endpoints + worker publish task.
- analytics: `AnalyticsSnapshot` model + analytics service/endpoints + worker sync placeholder.
- compliance: `ComplianceReport` model + compliance service + endpoints.
- YouTube OAuth: not found.
- media: `Asset`, `AssetLicense` models; no dedicated media API found in inspected routes.
- AI agents: `product_agents.py`.
- LLM calls: `LLMCall`, `LLMCostLedgerEntry`, tracked client abstraction.
- workflow/pipeline runs: `WorkflowRun`, `WorkflowStep`, `WorkflowEvent`, engine/service/worker tasks.

## 15) Duplicate or overlapping concepts
1. Dual repository implementations (`InMemoryVideoProjectRepository` + `DBVideoProjectRepository`) overlap behavior and can drift.
2. Workflow orchestration split across synchronous API service (`WorkflowEngine`) and Celery tasks with partially overlapping responsibilities.
3. Frontend domain types in `apps/frontend/lib/types.ts` overlap with generated OpenAPI DTOs and require manual mapping in `apiClient.ts`.
4. LLM/compliance concepts appear both as agent outputs and separate compliance service logic (possible policy drift).

## 16) Safe extension points
- Add new bounded contexts under `apps/backend/app/services/` with repo-backed persistence and explicit schemas.
- Add new API routers under `apps/backend/app/api/` and include from `main.py`.
- Extend DB via Alembic migrations in `apps/backend/alembic/versions`.
- Extend contract generation flow via `apps/backend/scripts/export_openapi.py` + `packages/shared` artifacts.
- Add new Celery tasks in `apps/worker/app/tasks/` leveraging existing idempotency primitives.

## 17) Do-not-touch list (high merge-conflict / high-coupling risk)
- `packages/shared/src/backend-api.ts` (generated; edit source OpenAPI instead).
- `packages/shared/openapi/backend.openapi.json` (generated contract artifact).
- `apps/frontend/lib/apiClient.ts` mapping logic unless backend contract changes are coordinated.
- `apps/backend/app/repositories/video_project_repository.py` (central cross-cutting persistence behavior).
- `apps/backend/app/schemas/video_project.py` (contract-critical; impacts FE/BE compatibility).
- Alembic history files (`apps/backend/alembic/versions/*`) — append-only migration discipline required.

## 18) Gaps blocking QualityTube OS implementation
- Missing real YouTube OAuth/account linking lifecycle.
- No concrete YouTube API client integration (upload, metadata patch, analytics ingestion are simulated/scaffolded).
- No first-class Topic/Brief domain and APIs.
- Limited media pipeline APIs (asset ingest/rights validation workflows incomplete).
- Agent framework currently mock-provider centric; no production LLM provider adapter/auth/guardrails.
- Unclear tenancy/auth hardening (identity dependency exists, but production auth model not fully evident from inspected files).

## 19) Recommended implementation sequence
1. **Contract-first alignment**: finalize schema payloads (especially approval/compliance/project detail fields), regenerate shared contracts, update frontend adapters.
2. **YouTube identity foundation**: OAuth domain models + token storage + channel linking APIs.
3. **Publishing hardening**: real upload pipeline with resumable upload states, retries, and quota accounting.
4. **Analytics ingestion**: scheduled sync tasks + normalization into `AnalyticsSnapshot`.
5. **Content planning domains**: Topic, Brief, Idea lifecycle APIs with approval gates.
6. **LLM provider productionization**: pluggable providers, policy filters, prompt/version tracking, deterministic audit trails.
7. **Compliance expansion**: rule packs for disclosure/copyright/repetitive-content checks tied to publish gates.
8. **Workflow unification**: clearly separate API orchestration vs async execution ownership.

## 20) Immediate risks and mitigation plan
- **Risk:** FE/BE contract drift (manual mapper + generated types).  
  **Mitigation:** enforce CI contract check as required gate; disallow manual payload fields not in OpenAPI.
- **Risk:** In-memory vs DB repo behavior divergence.  
  **Mitigation:** shared repository contract tests executed against both implementations.
- **Risk:** Simulated YouTube publish flow may create false confidence.  
  **Mitigation:** feature-flag “simulated publish” vs “real publish”; explicit environment banners.
- **Risk:** Compliance logic split and partial coverage.  
  **Mitigation:** centralize policy evaluation interface and versioned rule outputs.
- **Risk:** Workflow/event consistency across API and worker.  
  **Mitigation:** define event schema + idempotency contract and validate in integration tests.

---

## End-of-step output
- files created:
  - `docs/architecture/repo-reconnaissance.md`
- files changed:
  - `docs/architecture/repo-reconnaissance.md`
- tests run:
  - none (read-only reconnaissance via static inspection)
- known limitations:
  - No runtime verification performed.
  - Some repository methods/routes were inferred from partial file inspection where files were long.
  - This report explicitly marks YouTube OAuth as not found in inspected code paths.
- recommended next prompt:
  - “Implement Phase 1 contract-alignment: reconcile `ApprovalDecisionIn` payload between backend schemas and frontend `apiClient`, regenerate OpenAPI shared contracts, and add/update FE+BE tests to prevent regressions.”
