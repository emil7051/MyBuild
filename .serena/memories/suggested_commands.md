# Suggested Commands (updated 2026-02-06)

Use `bun` for frontend tasks.

Quick start:
- `python -m pip install -r requirements-dev.lock.txt`
- `python scripts/generate_vehicle_catalog_ts.py`
- `python scripts/validation.py`
- `uvicorn backend.app.main:app --reload`
- `cd frontend && bun install --frozen-lockfile && bun run dev`

Backend quality gates:
- `python -m pytest tests --cov`
- `mypy backend/app/core backend/app/api backend/app/main.py`
- `ruff check .`
- `black .`
- `isort .`

Frontend quality gates:
- `cd frontend && bun run test`
- `cd frontend && bun run lint`
- `cd frontend && bun run typecheck`
- `cd frontend && bun run build`
- `cd frontend && bun run test:e2e` (optional local smoke)

Dependency/security checks:
- `pip-audit -r requirements.lock.txt`
- `cd frontend && bun audit`