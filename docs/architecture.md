# Architecture

## Monorepo components
- `apps/frontend` — aplikacja Next.js (UI dla zespołu).
- `apps/backend` — FastAPI (API domenowe, workflow, compliance, usage).
- `apps/worker` — Celery worker (zadania async, publikacja/sync).
- `packages/shared` — miejsce na współdzielone kontrakty.

## Runtime architecture
1. Użytkownik pracuje w frontendzie i wykonuje akcje na VideoProject.
2. Frontend wywołuje backend API (`/api/v1/video-projects/...`).
3. Backend zapisuje stan i zdarzenia w PostgreSQL.
4. Worker wykonuje zadania asynchroniczne (np. publish/sync).
5. Redis pełni rolę brokera dla Celery.

## Kluczowe moduły backend
- `WorkflowEngine` — inicjuje i prowadzi kroki procesu.
- `ComplianceService` — ocena ryzyka i blokowanie publikacji.
- `UsageService` + `PlanLimitService` — limity planów i zużycie.
- `YouTubeQuotaService` — ledger quota per metoda API.
- `ModelRouter` + agenci — routing modeli i tracking kosztów.

## Data and governance
- PostgreSQL przechowuje encje domenowe (projekty, workflow, decyzje, ledgery kosztów/quota, analytics).
- Workflow emituje zdarzenia audytowe (`workflow_events`).
- Approval decisions są trwałym logiem decyzji użytkowników.
