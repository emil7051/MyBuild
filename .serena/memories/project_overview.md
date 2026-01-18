# TCO Web Platform overview

Purpose: Web platform for comparing total cost of ownership (TCO) of battery-electric vs diesel trucks over a 15-year lifecycle, aimed at truck operators, fleet managers, and TWU.

Key areas:
- Interactive wizard, scenario modeling, and visual insights for cost comparisons.
- Session persistence and analytics dashboard for aggregated insights.

High-level structure (monorepo):
- backend/: FastAPI app with API routes, DB models, services.
- frontend/: React + TypeScript UI (wizard/results).
- shared/: TypeScript calculator engine, generated data, shared types.
- data/: Authoritative Python data (vehicles, scenarios, policies, constants).
- scripts/: Generation/validation utilities.
- tests/: Backend test suite.
- docker-compose.yml: Local dev orchestration.
