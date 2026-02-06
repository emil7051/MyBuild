# Task completion checklist (updated 2026-02-06)

- Regenerate shared data/types when `data/*.py` changes: `python scripts/generate_vehicle_catalog_ts.py`.
- Run validation when vehicle/scenario/policy data changes: `python scripts/validation.py`.
- Keep TS calculator parity within ±1% of fixtures and include parity evidence in PRs.
- Run Python quality checks: `ruff check .`, `black .`, `isort .`.
- Run backend tests: `python -m pytest tests --cov`.
- Run frontend checks: `cd frontend && bun run test && bun run lint && bun run typecheck`.
- Run frontend build if release-facing changes are made: `cd frontend && bun run build`.
- Run dependency audits when dependencies change: `pip-audit -r requirements.lock.txt`, `cd frontend && bun audit`.
- Include `cd frontend && bun run test:e2e` for UI-flow-sensitive changes when feasible.