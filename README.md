# QualityTube OS

**Slogan:** *Create better YouTube videos with AI — not more spam.*

QualityTube OS is an **AI-assisted, human-approved, compliance-aware YouTube content operations system** for creators, teams, and agencies that want better content quality, stronger editorial control, and lower policy risk.

## Product name

QualityTube OS

## Short product description

QualityTube OS is an operations layer for research, scripting, review, publishing workflows, and analytics feedback in YouTube production environments where quality, originality, and policy compliance matter.

## Core philosophy

- AI accelerates execution, but humans own editorial decisions.
- Compliance is a first-class product requirement, not a post-processing step.
- Quality beats volume: repeatable systems should improve output standards, not flood platforms with low-value content.

## What the system does

- Supports structured planning and workflow orchestration.
- Provides AI-assisted research and script generation with mandatory human checkpoints.
- Enforces SEO and compliance review stages before publication.
- Coordinates publishing/scheduling pipelines.
- Tracks performance analytics and feeds insights back into planning.
- Monitors AI usage cost and YouTube API quota consumption.
- Enables team collaboration, ownership, and approval flows.

## What the system explicitly does not do

- Does not promise monetization outcomes.
- Does not automate channel growth without human work.
- Does not provide one-click, no-review mass content publishing.
- Does not position itself as a passive-income or “cash machine” tool.

## Target users

- YouTube creators with repeatable production workflows.
- Small in-house media teams.
- Content agencies operating multi-channel pipelines.
- Operators who need auditability, quality controls, and role-based approvals.

## Core modules

- Planning and briefing
- Research and script generation
- Compliance and quality review
- Approval workflow and sign-off
- Publishing/scheduling orchestration
- Analytics and feedback loop
- Cost/quota governance

## MVP scope

- End-to-end assisted pipeline for plan → draft → review → approve → publish.
- Baseline compliance checkpoints for YouTube policy-sensitive areas.
- Human approval requirements before publication.
- Analytics ingestion and basic performance feedback into future planning.

## Architecture overview

- `apps/frontend` — Next.js operator interface
- `apps/backend` — FastAPI orchestration and policy services
- `apps/worker` — Celery async task execution
- `packages/shared` — shared contracts/types placeholder
- `infra` — infrastructure scripts
- `docs` — product, compliance, and architecture documentation

## Local development quickstart

1. Copy environment:
   ```bash
   cp .env.example .env
   ```
2. Build and start:
   ```bash
   docker compose up --build
   ```

## Environment variables overview

- Local configuration is managed via `.env` (copied from `.env.example`).
- Variables configure frontend/backend runtime behavior, infrastructure endpoints, API credentials, and local feature settings.
- Treat secrets as sensitive and never commit secret values.

## Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend healthcheck: http://localhost:8000/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Testing commands

Run from repository root:

```bash
make test
make test-backend
make test-frontend
make lint
make typecheck
```

Backend coverage focus (pytest):
- model tests
- API tests
- workflow tests
- compliance tests
- LLM cost tracking tests
- approval tests
- quota tests

Frontend checks:
- TypeScript typecheck (`npm run typecheck`)
- lint (`npm run lint`)

CI (GitHub Actions) runs:
- backend lint/typecheck (`ruff check`, `mypy`)
- backend tests
- frontend typecheck
- frontend lint
- security checks (`pip-audit`, `npm audit --omit=dev`)
- docker build

## Compliance-first philosophy

QualityTube OS is designed around policy-aware operations. Compliance checks are embedded into workflow stages so content is reviewed before publication decisions, not after incidents.

## Human approval workflow

AI outputs are drafts, not final artifacts. Human reviewers must approve publish-ready assets and can reject, request revision, or escalate policy concerns.

## Quality gates

Quality gates enforce minimum standards for:
- originality and transformation value
- factual and editorial quality
- policy/compliance risk
- metadata and packaging quality

## Analytics feedback loop

Post-publication performance is used to refine briefs, scripting standards, packaging decisions, and workflow templates. The goal is continuous quality improvement over repeated production cycles.
