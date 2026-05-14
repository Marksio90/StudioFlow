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
- backend tests
- frontend typecheck
- docker build
