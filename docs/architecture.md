# Architecture Overview

## Core topology

- **Frontend (`apps/frontend`)**: Next.js UI shell
- **Backend (`apps/backend`)**: FastAPI control-plane API
- **Worker (`apps/worker`)**: Celery workers for asynchronous jobs
- **Data stores**:
  - PostgreSQL for durable domain data
  - Redis for queues, cache, and ephemeral coordination
- **Shared package (`packages/shared`)**: contracts/types between services

## Runtime orchestration

Docker Compose orchestrates local environment with healthchecks for:
- PostgreSQL
- Redis
- Backend (`/health`)
- Worker (Celery inspect ping)

## Principles

- Modular service boundaries
- Async-first job handling
- Human-in-the-loop checkpoints by design
- Cost and quota observability as first-class concerns
