# AI Media Operations OS

AI Media Operations OS is a B2B/SaaS workflow platform for YouTube creators, small teams, and agencies.

> This project is **not** a “no-face monetization machine” or auto-earn system.
> It is an operations layer for planning, quality control, publishing workflows, and analytics.

## Scope (foundation stage)

- Content planning and workflow orchestration
- AI-assisted research and script generation (with human approval)
- SEO and compliance checkpoints
- Publishing/scheduling pipeline
- Analytics and operational reporting
- AI cost control and YouTube API quota governance
- Team collaboration and approvals

## Current implementation status

### Frontend (`apps/frontend`)

- ✅ Next.js application starts and exposes the base UI shell.
- ⚠️ Data persistence is currently **mocked via `localStorage`** (no production API contract enforced end-to-end).
- ⚠️ Some views/components are in foundation mode and still rely on temporary/mock data flows.

### Backend (`apps/backend`)

- ✅ FastAPI service starts and exposes core routes (including healthcheck).
- ⚠️ Repository/persistence layer currently uses an **in-memory repository mock** for selected domains.
- ⚠️ Full production persistence hardening (migrations, transactional guarantees, operational policies) is still in progress.

### Worker (`apps/worker`)

- ✅ Celery worker starts and passes container healthcheck.
- ⚠️ Background jobs include **placeholder task implementations** (stub logic for async pipelines).
- ⚠️ Production-grade retry/idempotency and long-running workflow resilience are not fully completed.

## Monorepo layout

- `apps/frontend` — Next.js app
- `apps/backend` — FastAPI API
- `apps/worker` — Celery async worker
- `packages/shared` — shared contracts/types placeholder
- `infra` — infra scripts
- `docs` — product and architecture docs

## Quick start

1. Copy environment:
   ```bash
   cp .env.example .env
   ```
2. Build and start:
   ```bash
   docker compose up --build
   ```

## Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend healthcheck: http://localhost:8000/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Acceptance baseline

- `docker compose up --build` starts all services
- FastAPI responds on `/health`
- Next.js frontend starts successfully
- Celery worker starts and passes container healthcheck

## Production-ready transition checklist

- [ ] Frontend no longer relies on `localStorage` mocks for core workflows; all critical flows run against versioned backend APIs.
- [ ] Backend in-memory repositories are replaced with durable PostgreSQL-backed implementations and covered by migration strategy.
- [ ] Worker placeholder tasks are replaced by real pipeline tasks with explicit input/output contracts.
- [ ] End-to-end tests cover at least one full content lifecycle (plan → generate → approve → publish).
- [ ] Observability is enabled: structured logs, metrics, tracing, and alerting for FE/BE/worker.
- [ ] Security baseline passes in CI: dependency scans, secret scanning, authz checks, and hardened config defaults.
- [ ] Retry/idempotency policy is defined and validated for all async jobs.
- [ ] Runbooks exist for incident response, rollback, and degraded-mode operations.
- [ ] SLO/SLA targets are defined with error budgets and quota/cost guardrails.

## Quality gates i testy

Uruchamianie lokalne z poziomu repo:

```bash
make test
make test-backend
make test-frontend
make lint
make typecheck
```

Zakres backend (pytest):
- testy modeli
- testy API
- testy workflow
- testy compliance
- testy LLM cost tracking
- testy approval
- testy quota

Frontend:
- TypeScript typecheck (`npm run typecheck`)
- lint (`npm run lint`)

CI (GitHub Actions) uruchamia:
- backend lint/typecheck (`ruff check`, `mypy`)
- backend tests
- frontend typecheck
- frontend lint
- security checks (`pip-audit`, `npm audit --omit=dev`)
- docker build
