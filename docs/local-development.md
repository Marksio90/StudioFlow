# Local Development

## Wymagania
- Docker + Docker Compose
- Make (opcjonalnie, do skrótów)

## Start środowiska
1. Skopiuj env:
   ```bash
   cp .env.example .env
   ```
2. Uruchom stack:
   ```bash
   docker compose up --build
   ```

## Endpointy lokalne
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Testy i jakość
```bash
make test
make test-backend
make test-frontend
make lint
make typecheck
```

## Jak rozwijać moduły
- **Backend API**: dodawaj endpointy w `apps/backend/app/api` i serwisy w `apps/backend/app/services`.
- **Workflow/compliance**: nowe kroki i reguły implementuj w `workflow_engine.py` i `compliance_service.py`.
- **Agenci AI**: rozszerz modele wejścia/wyjścia i routing modeli (`model_router.py`).
- **Worker**: zadania asynchroniczne dodawaj w `apps/worker/app/tasks`.
- **Kontrakty współdzielone**: docelowo `packages/shared`.

## Dobre praktyki dla nowych devów
- Traktuj `WorkflowEvent` i ledgery jako źródło audytu.
- Nie omijaj approval/compliance przy zmianach flow publikacji.
- Każdą integrację zewnętrzną instrumentuj pod koszt/limit.
