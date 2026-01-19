# Task completion checklist

- Regenerate shared data/types when data/*.py changes: python scripts/generate_vehicle_catalog_ts.py.
- Run validation when vehicle/scenario/policy data changes: python scripts/validation.py.
- Keep TS calculator parity within ±1% of fixtures; include parity evidence in PRs.
- Run Python format/lint: ruff check ., black ., isort .
- Run tests: python -m pytest tests --cov; cd frontend && bun test.
- Run frontend checks: bun run lint; bun run typecheck; bun run build (if relevant).
- If dependencies change, run pip-audit, bun audit (if using Bun), and bandit.
