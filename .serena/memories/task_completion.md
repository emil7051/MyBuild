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

## 2026-02-07 refactor verification addendum
- Verified `CODEBASE_AUDIT_AND_REFACTOR_PLAN.md` completion status with parallel sub-agent review across backend/frontend/shared/CI scopes.
- Resolved residual migration tech-debt in active runtime paths:
  - removed `sessionSecretHash` cache compatibility fallback (`backend/app/core/cache.py`)
  - removed legacy `setIsCalculating` store API (`frontend/src/state/tcoStore.ts`)
  - finalized non-persistence of `results` payload in local storage (`frontend/src/state/tcoStore.ts`)
- Validation checks used for this cleanup:
  - `python -m pytest tests/test_cache.py`
  - `cd frontend && bun run test src/test/state-management.test.ts`
  - `cd frontend && bun run typecheck`
