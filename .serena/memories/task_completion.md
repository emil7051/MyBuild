# Task completion checklist

- Regenerate shared data/types when data/*.py changes: python scripts/generate_vehicle_catalog_ts.py.
- Run validation when vehicle/scenario/policy data changes: python scripts/validation.py.
- Keep TS calculator parity within ±1% of fixtures; include parity evidence in PRs.
- Run Python format/lint: ruff check ., black ., isort .
- Run tests: python -m pytest tests --cov; cd frontend && npm run test.
- Run frontend checks: npm run lint; npm run typecheck; npm run build (if relevant).
- If dependencies change, run pip-audit, npm audit, and bandit.
