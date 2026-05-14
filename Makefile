.PHONY: test test-backend test-frontend lint typecheck

test: test-backend test-frontend

test-backend:
	cd apps/backend && pytest

test-frontend:
	cd apps/frontend && npm run typecheck

lint:
	cd apps/frontend && npm run lint

typecheck:
	cd apps/frontend && npm run typecheck
