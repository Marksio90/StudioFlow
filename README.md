# QualityTube OS

**Slogan:** *Create better YouTube videos with AI — not more spam.*

QualityTube OS is an **AI-assisted, human-approved, compliance-aware YouTube content operations system** for partners, agencies, and creator teams that prioritize editorial quality, operational consistency, and policy safety.

## Current implementation status

QualityTube OS is currently implemented as an MVP-oriented operations stack that supports a full assisted workflow from planning through publication, with mandatory human decision points and baseline policy controls.

## MVP boundary

The MVP is intentionally constrained to high-value workflow orchestration, review controls, and performance feedback. It is not a growth-hacking engine, not an autonomous content farm, and not a substitute for editorial leadership.

## Quickstart

Run from repository root:

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
2. Build and start all services:
   ```bash
   docker compose up --build
   ```

## Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend healthcheck: http://localhost:8000/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Environment variables

- Local configuration is managed through `.env` (copied from `.env.example`).
- Variables cover frontend/backend runtime behavior, infrastructure endpoints, API credentials, and local feature flags.
- Treat all secrets as sensitive and never commit secret values.

## Testing and quality checks

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

Frontend quality checks:
- TypeScript typecheck (`npm run typecheck`)
- lint (`npm run lint`)

CI (GitHub Actions) runs:
- backend lint/typecheck (`ruff check`, `mypy`)
- backend tests
- frontend typecheck
- frontend lint
- security checks (`pip-audit`, `npm audit --omit=dev`)
- docker build

## Architecture summary

- `apps/frontend` — Next.js operator interface
- `apps/backend` — FastAPI orchestration and policy services
- `apps/worker` — Celery async task execution
- `packages/shared` — shared contracts/types placeholder
- `infra` — infrastructure scripts
- `docs` — product, compliance, and architecture documentation
  - Channel Workspace: `docs/product/channel-workspace.md`

## Compliance and approval workflow

### Compliance model

- Compliance is a first-class product requirement, not post-processing.
- Policy-aware checks are embedded in workflow stages before publication decisions.
- Quality gates enforce minimum standards for originality, factual quality, policy risk, and metadata packaging.

### Human approval model

- AI outputs are draft assets only.
- Human reviewers own final editorial and publication decisions.
- Reviewers can approve, reject, request revisions, or escalate policy concerns.

### Performance feedback loop

- Post-publication analytics feed back into briefing, scripting standards, packaging choices, and workflow templates.
- The operating objective is sustained quality improvement across repeated production cycles.

## Explicit platform and monetization disclaimers

QualityTube OS explicitly rejects the following positioning and use cases:

- Spam automation or mass low-value content production.
- Passive-income promises or “set-and-forget” channel automation narratives.
- Guaranteed monetization, guaranteed growth, or guaranteed revenue claims.

The system is designed for disciplined teams that combine AI leverage with accountable human judgment.
