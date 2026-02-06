# TCO Web Platform overview (updated 2026-02-06)

Purpose:
- Web platform for comparing total cost of ownership (TCO) of BEV vs diesel trucks over a 15-year lifecycle.

Current architectural decisions:
- Shared TypeScript calculator (`shared/calculator`) is the source of truth for calculations.
- Deployment target is Replit autoscale with Replit-managed PostgreSQL.
- Docker/compose hardening findings are de-scoped for current repository deployment posture.
- Session read/update is authorized via HttpOnly session-secret cookie (SHA-256 hash at rest).
- Backend observability baseline is implemented: structured request logs, `x-request-id`, sampled tracing (`x-trace-id` on sampled requests), metrics, and alert events.

Monorepo structure:
- `backend/`: FastAPI API for vehicles, sessions, analytics, middleware/security/observability.
- `frontend/`: React + TypeScript app (wizard + results) using shared calculator.
- `shared/`: calculator, generated data catalogs, shared type contracts.
- `data/`: authoritative Python constants/vehicles/scenarios/policies.
- `scripts/`: generation + validation utilities.
- `tests/`: backend tests.

Key docs:
- `README.md`, `API.md`, `replit.md`, `docs/replit-deployment-runbook.md`, `docs/security-requirements.md`, `SECURITY.md`.