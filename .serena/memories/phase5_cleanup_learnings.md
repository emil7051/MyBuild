# Phase 5 Cleanup Learnings

## Date: 2026-01-19

## Key Findings

### Items Already Complete in Previous Phases
Several audit items flagged for Phase 5 were already addressed:
- `calculateBatteryHealth` dead code - removed in earlier phases
- Preview runner hook in WizardCompareStep - already removed
- FastAPI `on_event` hooks - already migrated to lifespan in `main.py`
- Pydantic v1 `@validator` - already using `field_validator` (v2 syntax)
- Legacy code (`CalculationRequest`, `ComparisonRequest`, `to_engine_overrides`) - not present in codebase
- README migration instructions - already updated with Alembic

### Actual Changes Made

1. **getVehicleCatalogSnapshot**: Updated to return `{version, vehicles}` for cache invalidation
2. **Duty cycle fallback**: Fixed from 40/35/25 to 60/25/15 (matching store defaults)
3. **SensitivityTornadoChart**: Added "approximate" labeling with explanation
4. **Python dependencies**: Synchronized versions, added organization comments
5. **Package manager docs**: Updated to use bun consistently

### Testing Notes
- vitest config already excludes e2e, but bun test picks them up anyway
- Use `npx vitest run` or check package.json scripts for proper test execution
- E2E tests use Playwright, not vitest - run separately

### Dependency Management
- `backend/requirements.txt` is minimal runtime deps for Docker
- `requirements.txt` includes additional data analysis tools for local dev
- `requirements-dev.txt` has testing and development tools
- greenlet version was inconsistent (3.0.0 vs 3.3.0) - synchronized to 3.3.0
