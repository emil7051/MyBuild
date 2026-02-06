# Codebase Audit and Refactor Plan

**Date:** 2026-02-06
**Auditor:** Claude Opus 4.5 (automated, multi-agent)
**Scope:** Full monorepo: backend, frontend, shared calculator, data layer, infrastructure

---

## 1. Executive Summary

This audit identified **86 findings** across the TCO Web Platform (75 from automated multi-agent analysis, 11 additional from a targeted follow-up review). The codebase is in reasonable shape for an early-stage product built with AI assistance. Linting, formatting, and dependency vulnerability scans all pass. The shared calculator engine has strong test coverage and Python-TypeScript parity verification.

**What matters most:**

1. **Test infrastructure and coverage still need work.** Core parity/unit suites are strong and CI now includes dedicated backend type-check and frontend E2E jobs, but component-test coverage remains thin.

2. **Deployment and observability guidance has improved, with remaining gaps.** A formal Replit deployment runbook now exists, and a low-overhead structured logging + request-metrics baseline is in place. Distributed tracing and alerting workflows remain the primary observability gap.

3. **AI-generated code patterns** are present but manageable. Repetitive sanitization code, defensive null checks on guaranteed types, and silent error swallowing add maintenance burden and UX risk.

---

## 2. Repo Overview

### Architecture Map

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                   │
│  React 18 + TypeScript + Vite + TailwindCSS          │
│  State: Zustand + React Query                        │
│  Port: 5000                                          │
│  Entry: frontend/src/main.tsx                        │
│  Routes: frontend/src/App.tsx                        │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP (Axios)
┌───────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI)                    │
│  Python 3.11 + SQLAlchemy + Pydantic                 │
│  Port: 8000                                          │
│  Entry: backend/app/main.py                          │
│  Routes: backend/app/api/router.py                   │
└───────────┬────────────────┬────────────────────────┘
            │                │
   ┌────────▼────┐    ┌─────▼──────┐
   │  PostgreSQL  │    │   Redis     │
   │  Port: 5432  │    │  Port: 6379 │
   └─────────────┘    └────────────┘

┌─────────────────────────────────────────────────────┐
│              Shared Calculator (TypeScript)           │
│  Source of truth for TCO calculations                │
│  Entry: shared/calculator/tcoCalculator.ts           │
│  Math: shared/calculator/math.ts                     │
│  Types: shared/types/tco.types.ts                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│             Python Data Layer (source of truth)       │
│  data/constants.py, vehicles.py, scenarios.py,       │
│  policies.py                                         │
│  Generator: scripts/generate_vehicle_catalog_ts.py   │
│  Output: shared/data/*.generated.ts                  │
└─────────────────────────────────────────────────────┘
```

### Key Entry Points

| Component | Entry Point | Evidence |
|-----------|-------------|----------|
| Frontend boot | `frontend/src/main.tsx` | SPA entry |
| Frontend routing | `frontend/src/App.tsx` | React Router |
| Backend app factory | `backend/app/main.py` | FastAPI + middleware |
| API routes | `backend/app/api/router.py` | All endpoints |
| Calculator engine | `shared/calculator/tcoCalculator.ts` | Core TCO logic |
| Data generation | `scripts/generate_vehicle_catalog_ts.py` | Python to TS |
| CI pipeline | `.github/workflows/ci.yml` | 5 jobs |

### Dependency Map

**Backend:** FastAPI 0.128 + SQLAlchemy 2.0.25 + Alembic 1.13 + asyncpg + Redis 5.0 + slowapi
**Frontend:** React 18 + React Query 5 + Zustand 4 + React Hook Form 7 + Zod 3 + Recharts 2 + Vite 7 + Vitest 4
**Shared:** Pure TypeScript, no external deps

---

## 3. Current Risk Snapshot

| Area | Risk Level | Status |
|------|------------|--------|
| Test coverage and CI safety rails | **Medium** | Core parity/unit suites are strong and CI now runs backend type-check + frontend E2E, but component and broader integration coverage remain limited. |
| Deployment and operations | **Low-Medium** | Replit deployment runbook is now documented; observability baseline exists but tracing/alerting maturity is still limited. |
| Code maintainability | **Low-Medium** | Major duplication/dead-code cleanup is complete; targeted AI-pattern refactors remain. |

---

## 4. Findings

### 4.1 Tests & Observability

#### OBS-01: Baseline observability implemented; tracing/alerting still pending
- **Evidence:** Backend now includes structured JSON request logs and in-memory request metrics with periodic summaries (`backend/app/core/observability.py`) wired through app middleware (`backend/app/main.py`). API-path request IDs are emitted in response headers (`x-request-id`). No OpenTelemetry/Prometheus/Sentry integration is configured yet.
- **Impact:** Request-level troubleshooting is improved with low overhead on key API paths. Cross-service traces and production alerting remain limited.
- **Recommendation:** Keep the current low-overhead logging baseline; add sampled distributed tracing and alerting workflows as a separate follow-up when operational maturity requires it.

## 5. Prioritized Backlog

| ID | Title | Impact | Effort | Risk | Phase | Dependencies |
|----|-------|--------|--------|------|-------|-------------|
| A11Y-01 | Add chart text alternatives | **Low** | M | Low | 3 | None |
| A11Y-02 | Replace chip pseudo-buttons with `<button>` | **Low** | S | Low | 3 | None |
| OBS-02 | Add sampled tracing + alerting workflow (Replit-compatible) | **Low** | M | Low | 3 | Build on OBS-01 baseline |

*Size: XS=<1hr, S=1-4hr, M=4-16hr, L=16hr+*

---

## 6. Migration Plan

### Phase 2: Low-Risk Refactors (3-5 days)

**Test and CI improvements:**

Remaining:
1. None

**Cleanup and maintenance:**

Remaining:
1. None

### Phase 3: Structural Improvements (ongoing)

**Goal:** Larger improvements that require more coordination. Execute as capacity allows.

1. Add component tests using React Testing Library
2. Add accessibility improvements (charts, stepper, error messages)
3. Add sampled distributed tracing and operational alerting

**Approach:** Use feature flags or route-level code splitting for lazy loading.

**Note on deployment:** Production runs on Replit with a Replit-managed database. Docker-compose-specific findings are de-scoped because Docker manifests are no longer active in this repository.

---

## 7. Tooling & Guardrails Recommendations

### Automate in CI (new checks)

| Check | Tool | Config |
|-------|------|--------|
| Python type checking | mypy | Add `backend-typecheck` job |
| SAST security scan | bandit | `bandit -r backend/ -ll` in lint job |
| Generated file staleness | Custom script | Regenerate + `git diff --exit-code` |
| Frontend formatting | prettier | Optional: if Prettier is reintroduced, enforce with `prettier --check src/`; DEP-04 removed the unused formatter for now. |
| Frozen lockfile | bun | `bun install --frozen-lockfile` |
| Constants validation | Custom | Charging mix sums, rate ranges, trajectory lengths |

### Pre-commit hooks (recommended)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.x  # pin to same version as CI
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

---

## 8. Open Questions & Assumptions

### Decisions Made

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | Fuel tax credit (CALC-03) | **Done.** Subtract $0.203/L from diesel cost. | Heavy vehicle operators can claim the credit. Not applying it overstates diesel costs by ~10%. |
| 2 | Annuity convention (CALC-01) | **Done.** Use annuity-due by multiplying result by `(1 + r)`. | More accurate for costs incurred throughout the year. ~5% correction to displayed annual costs. |
| 3 | Road user charges (CALC-04) | **Done.** Implement as optional BEV toggle, default OFF. | Keeps current policy baseline unchanged while enabling configurable RUC modelling. |
| 4 | Maintenance cost (CALC-08) | **Use weight-class constants.** Remove per-vehicle field from catalog. | Simpler. Eliminates the confusing mismatch between displayed and calculated values. |
| 5 | Cost breakdown structure (CALC-06) | **Restructure into named groups.** | Breaking change completed and moved to `DONE`; it removed ambiguity from mixed-basis chart data. |
| 6 | PaybackChart (FE-03) | **Year-by-year cash flows.** | Users are making $200k+ purchasing decisions. Accuracy matters. |
| 7 | Deployment target | **Replit + Replit-managed database.** | Docker hardening items deprioritised accordingly. |

### Assumptions (verified or updated)

- **Deployment target:** Replit with Replit-managed database. **Confirmed.** Docker hardening items are dev-environment-only improvements.
- **User base scale:** Recommendations assume moderate traffic (tens to low hundreds of concurrent users). Current implementation uses SHA-256 session-secret verification and avoids previous bcrypt CPU overhead in request paths.
- **PostgreSQL version:** Replit-managed PostgreSQL version may vary by environment; no active Docker-compose pin exists in this repository.
- **Browser support:** No browserslist config found beyond the env var workaround. Assumed modern browsers (Chrome/Firefox/Safari/Edge latest 2 versions).
- **Session secret migration:** Completed. Session secret is cookie-only and not returned in JSON responses.
- **Analytics performance targets:** No SLOs for analytics endpoints found. BE-03 was implemented with a single aggregate query; revisit only if business-level analytics SLOs are introduced.
- **Observability baseline:** Structured JSON request logging, request IDs, and lightweight per-route metrics are now implemented in backend middleware; tracing and alerting remain future work.
- **Dependency update tooling:** Dependabot automation is now configured via `.github/dependabot.yml` (pip, npm, and GitHub Actions ecosystems).

---

## 9. Appendix

### Baseline Health Snapshot (2026-02-06)

| Check | Status | Details |
|-------|--------|---------|
| Ruff (Python lint) | **PASS** | Clean |
| Black (formatting) | **PASS** | 43 files unchanged |
| isort (imports) | **PASS** | Clean |
| Backend tests (pytest) | **PASS** | `.venv/bin/python -m pytest tests --cov` passes (`64 passed`) |
| Data validation | **PASS** | 16 vehicles, 3 scenarios validated |
| TypeScript typecheck | **PASS** | Clean |
| ESLint (frontend) | **PASS** | Clean |
| Frontend tests (Vitest) | **PASS** | `bun run test` passes (`216/216`) with `jsdom` environment and expanded verification fixtures |
| Bandit (security) | **BROKEN** | Missing `pbr` module dependency |
| pip-audit (vulns) | **PASS** | No known vulnerabilities |
| Vulture (dead code) | **PASS** | Nothing detected at 80% confidence |
| mypy (type check) | **PASS** | `backend-typecheck` scope passes in CI path (`python -m mypy backend/app/core backend/app/api backend/app/main.py`) |

### Key Files Referenced

| Area | Key Files |
|------|-----------|
| Calculator engine | `shared/calculator/tcoCalculator.ts`, `shared/calculator/math.ts` |
| Type contracts | `shared/types/tco.types.ts` |
| Data source of truth | `data/constants.py`, `data/vehicles.py`, `data/scenarios.py`, `data/policies.py` |
| Generated data | `shared/data/constants.generated.ts`, `shared/data/vehicleCatalog.ts`, `shared/data/scenarios.ts` |
| Frontend state | `frontend/src/state/tcoStore.ts`, `frontend/src/hooks/useCalculations.ts` |
| Backend entry | `backend/app/main.py`, `backend/app/api/router.py` |
| Backend services | `backend/app/services/sessions.py`, `backend/app/core/cache.py`, `backend/app/core/security.py` |
| CI pipeline | `.github/workflows/ci.yml`, `.github/workflows/dependency-audit.yml` |
| Tests | `tests/`, `frontend/src/test/`, `shared/calculator/verification_data.json` |

---

## 10. DONE

Completed items moved from active backlog/planning lists.

| ID | Status | Completed | Notes |
|----|--------|-----------|-------|
| CALC-01 | **DONE** | 2026-02-06 | Updated annualisation to annuity-due in `shared/calculator/math.ts`; refreshed verification fixtures/tests. |
| CALC-02 | **DONE** | 2026-02-06 | Fixed articulated BEV charging mix sum to 1.0 in `data/constants.py`; added charging-mix validation in `scripts/validation.py`. |
| CALC-03 | **DONE** | 2026-02-06 | Applied diesel fuel tax credit in `shared/calculator/tcoCalculator.ts`; refreshed verification fixtures/tests. |
| CALC-04 | **DONE** | 2026-02-06 | Implemented BEV road user charge as a toggleable override (default OFF) across shared types, frontend, backend model, and calculator logic. |
| CALC-05 | **DONE** | 2026-02-06 | Aligned Python and TypeScript rebate calculation logic. |
| CALC-06 | **DONE** | 2026-02-06 | Restructured cost breakdown into named groups (`npv_costs`, `nominal_costs`, `upfront_costs`). |
| CALC-07 | **DONE** | 2026-02-06 | Added `BATTERY_REPLACEMENT_YEAR = 8` to `data/constants.py`. |
| CALC-08 | **DONE** | 2026-02-06 | Removed the misleading `maintenance_cost_per_km` field from the vehicle catalog data to avoid showing users a number that doesn't drive calculations. |
| TEST-01 | **DONE** | 2026-02-06 | Resolved local backend test infrastructure; `.venv/bin/python -m pytest tests --cov` now passes with `pytest==8.4.2` and `pytest-asyncio==1.3.0`. |
| TEST-02 | **DONE** | 2026-02-06 | Excluded `e2e/` from Vitest and corrected module reset usage in frontend tests; suite now runs cleanly. |
| TEST-03 | **DONE** | 2026-02-06 | Switched Vitest to `jsdom` in `frontend/vitest.config.ts` and added `jsdom` dev dependency; frontend tests continue to pass. |
| TEST-04 | **DONE** | 2026-02-06 | Regenerated `shared/calculator/verification_data.json` to include all scenarios (`baseline`, `technology_breakthrough`, `oil_crisis`) with full vehicle/purchase coverage. |
| TEST-05 | **DONE** | 2026-02-06 | Added multiple override fixture combinations (5 total) covering diesel/BEV, vehicle overrides, and financed/outright purchase methods. |
| TEST-06 | **DONE** | 2026-02-06 | Added request-size middleware tests for oversized `Content-Length` and chunked bodies, including side-effect prevention checks (`tests/test_middleware.py`). |
| TEST-07 | **DONE** | 2026-02-06 | Added rate-limit integration coverage to verify `429` when the vehicle endpoint exceeds configured per-minute limits (`tests/test_api.py`). |
| TEST-08 | **DONE** | 2026-02-06 | Added session update authorization tests for missing secret cookie (`401`) and wrong secret cookie (`403`) (`tests/test_api.py`). |
| TEST-09 | **DONE** | 2026-02-06 | Removed shared-state mutation risk in carbon-cost test by cloning the baseline scenario and restoring the original scenario reference (`frontend/src/test/calculator/carbon-cost.test.ts`). |
| TEST-10 | **DONE** | 2026-02-06 | Added a dedicated `backend-typecheck` CI job in `.github/workflows/ci.yml` and configured mypy via `pyproject.toml` for explicit package bases and reproducible CI execution. |
| TEST-11 | **DONE** | 2026-02-06 | Added a `frontend-e2e` CI job in `.github/workflows/ci.yml` that installs Chromium and runs Playwright smoke tests (`frontend/e2e/smoke.spec.ts`) with report artifact upload. |
| FE-01 | **DONE** | 2026-02-06 | Added a top-level React error boundary with fallback and retry/reload actions (`frontend/src/components/shared/ErrorBoundary.tsx`, wired in `frontend/src/main.tsx`). |
| FE-02 | **DONE** | 2026-02-06 | Integrated `VehicleParamsForm` into React Hook Form by adding `vehicleParamOverrides` to the shared schema and step validation flow (`frontend/src/forms/wizardForm.ts`, `frontend/src/pages/WizardPage.tsx`, `frontend/src/components/wizard/VehicleParamsForm.tsx`). |
| FE-03 | **DONE** | 2026-02-06 | Replaced simplified payback interpolation with year-by-year nominal cash-flow timelines via shared calculator helper (`shared/calculator/tcoCalculator.ts`, `frontend/src/components/results/PaybackChart.tsx`). |
| PERF-01 | **DONE** | 2026-02-06 | Added route/component code splitting via `React.lazy` + `Suspense` for `ResultsPage` and results chart modules (`frontend/src/App.tsx`, `frontend/src/components/results/ResultsPanel.tsx`). |
| PERF-02 | **DONE** | 2026-02-06 | Added an `Intl.NumberFormat` cache keyed by normalized options to avoid per-render formatter creation (`frontend/src/utils/format.ts`). |
| PERF-03 | **DONE** | 2026-02-06 | Removed per-chart Zustand subscriptions by lifting state reads into `ResultsPanel` and passing memoized props/data into chart components. |
| PERF-04 | **DONE** | 2026-02-06 | Removed heavy optional analysis packages from runtime `requirements.txt` and moved them to `requirements-scripts.txt` (adapted from Docker framing, since Docker was removed). |
| MAINT-01 | **DONE** | 2026-02-06 | Pinned ruff consistently to `ruff==0.8.0` in `requirements-dev.txt` and `.github/workflows/ci.yml`. |
| MAINT-02 | **DONE** | 2026-02-06 | Consolidated Python lint tooling on ruff by removing `flake8` (+ plugins) and `pylint` from `requirements-dev.txt`. |
| MAINT-03 | **DONE** | 2026-02-06 | Added missing test dependencies (`anyio`, `httpx`, `factory-boy`) to `requirements-dev.txt` so local test installs match CI needs. |
| MAINT-04 | **DONE** | 2026-02-06 | Removed duplicated constants from `shared/data/constants.future.ts`; `FUTURE_CONSTANTS` now remains an empty reserved object until future-only constants are introduced. |
| MAINT-05 | **DONE** | 2026-02-06 | Deleted unused `frontend/src/components/wizard/WizardVehicleStep.tsx` (orphaned component with no imports). |
| MAINT-06 | **DONE** | 2026-02-06 | Extracted `buildComparisonPayload(wizardData)` in `frontend/src/utils/payload.ts` and updated `WizardCompareStep` + `AppShell` to consume the single shared builder; added payload utility tests for dedupe/compaction behavior. |
| MAINT-07 | **DONE** | 2026-02-06 | Enabled `plugin:react-hooks/recommended` in `frontend/.eslintrc.cjs` and resolved the resulting exhaustive-deps warning in `frontend/src/components/results/PaybackChart.tsx`. |
| MAINT-08 | **DONE** | 2026-02-06 | Updated `scripts/generate_vehicle_catalog_ts.py` to generate a strongly-typed `ConstantsSchema` interface directly from Python constants; `shared/data/constants.generated.ts` now exports typed schema + constants. |
| MAINT-09 | **DONE** | 2026-02-06 | Standardized Redis cache entries to snake_case (`session_secret_hash`) in `backend/app/core/cache.py` with a legacy read fallback for existing camelCase cache entries. |
| MAINT-10 | **DONE** | 2026-02-06 | Added formula documentation (mathematical notation + source references) for payload penalty, monthly finance payments, and residual value in `shared/calculator/tcoCalculator.ts`. |
| MAINT-11 | **DONE** | 2026-02-06 | Replaced hard-coded calculator sanitization limits with shared `OVERRIDE_LIMITS` values in `shared/calculator/tcoCalculator.ts`, preserving the below-min reject behavior for `annual_kms_variation`. |
| MAINT-12 | **DONE** | 2026-02-06 | Unified duty-cycle validation policy across store/form payload flow, shared calculator, and backend contract boundaries. Removed silent store corrections, blocked invalid payloads in frontend builders/autosave, and made calculator reject invalid duty cycles with explicit errors. |
| AI-01 | **DONE** | 2026-02-06 | Refactored calculator override sanitization to a data-driven helper over `OVERRIDE_LIMITS`, preserving `annual_kms_variation` special handling via `clampOverrideAboveMin` (`shared/calculator/tcoCalculator.ts`), and added regression coverage (`frontend/src/test/calculator/override-sanitization.test.ts`). |
| AI-02 | **DONE** | 2026-02-06 | Removed defensive wizard override fallbacks in frontend form/payload paths and enforced initialized override objects in store updates/rehydration (`frontend/src/pages/WizardPage.tsx`, `frontend/src/utils/payload.ts`, `frontend/src/state/tcoStore.ts`). |
| AI-03 | **DONE** | 2026-02-06 | Removed low-signal comments that restated implementation details in touched frontend files (`frontend/src/pages/WizardPage.tsx`, `frontend/src/components/results/ResultsPanel.tsx`). |
| AI-04 | **DONE** | 2026-02-06 | Removed audit reference code tags from test comments/docstrings to keep code narrative focused (`tests/test_security.py`, `tests/test_services.py`). |
| AI-05 | **DONE** | 2026-02-06 | Removed reachable-branch `# pragma: no cover` markers and added explicit 404 coverage for unknown session get/update paths (`backend/app/api/router.py`, `backend/app/services/vehicles.py`, `tests/test_api.py`). |
| AI-06 | **DONE** | 2026-02-06 | Replaced hand-rolled payload hashing with `fast-json-stable-stringify` in calculation dedupe logic and preserved `undefined`/`null` distinction with a sentinel replacer (`frontend/src/hooks/useCalculations.ts`, `frontend/package.json`). |
| AI-07 | **DONE** | 2026-02-06 | Surfaced calculation/persist failures via toast notifications and added transient retry behavior for session create/update calls (including pending flushes), with retry coverage tests (`frontend/src/hooks/useCalculations.ts`, `frontend/src/services/sessionLifecycle.ts`, `frontend/src/test/sessionLifecycle.test.ts`). |
| DEAD-01 | **DONE** | 2026-02-06 | Confirmed runtime dependencies are slim and optional heavy analysis packages remain isolated in `requirements-scripts.txt` (`numpy`, `numpy-financial`, `pandas`, `plotly`, `rich`, `click`). |
| DEAD-02 | **DONE** | 2026-02-06 | Removed unused dev-only dependencies from `requirements-dev.txt` (`tox`, `sphinx`, `sphinx-rtd-theme`, `jupyter`, `ipykernel`, `memory-profiler`, `line-profiler`, `py-spy`, `safety`, `interrogate`). |
| DEAD-03 | **DONE (N/A IN THIS PLAN)** | 2026-02-06 | No standalone `DEAD-03` finding exists in this document; historical dependency cleanup (`orjson`, `marshmallow`, `cerberus`, `loguru`) is already reflected in current requirements files. |
| DEAD-04 | **DONE** | 2026-02-06 | Removed vestigial `useVehicleCatalog` hook and replaced consumers with direct `VEHICLE_SUMMARIES` imports in `WizardDieselStep` and `WizardElectricStep`. |
| DEAD-05 | **DONE** | 2026-02-06 | Consolidated backend security/audit requirements into `docs/security-requirements.md` and removed in-code audit reference tags (`SEC-*`, `API-*`) from backend docstrings/comments. |
| DEAD-06 | **DONE** | 2026-02-06 | Removed unused `fetchSession` helper from `frontend/src/services/api.ts`. |
| DEAD-07 | **DONE** | 2026-02-06 | Removed dead `ValueError` exception branch from session creation in `backend/app/api/router.py`. |
| DEP-01 | **DONE** | 2026-02-06 | Migrated frontend linting to ESLint 9 + `typescript-eslint` v8 flat config (`frontend/eslint.config.js`), upgraded related ESLint packages, and removed legacy `.eslintrc.cjs`. |
| DEP-02 | **DONE** | 2026-02-06 | Updated core Python dependency pins: `fastapi` (0.128.2), `sqlalchemy` (2.0.46), `pytest` (8.4.2), `black` (24.10.0), and `mypy` (1.19.1). |
| DEP-03 | **DONE** | 2026-02-06 | Removed explicit `greenlet` runtime pin from `requirements.txt` to avoid SQLAlchemy upgrade resolver conflicts. |
| DEP-04 | **DONE** | 2026-02-06 | Removed unused frontend Prettier dependency and config (`frontend/package.json`, `frontend/.prettierrc`) rather than carrying an unenforced formatter. |
| DEP-05 | **DONE** | 2026-02-06 | Added `--frozen-lockfile` to all CI/frontend `bun install` steps in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`. |
| DEP-06 | **DONE** | 2026-02-06 | Pinned `BUN_VERSION` to `1.3.5` in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml` for reproducible builds. |
| DEP-07 | **DONE** | 2026-02-06 | Added automated dependency update workflow via `.github/dependabot.yml` with monthly runtime updates and separate security update grouping. |
| OPS-01 | **DONE** | 2026-02-06 | Added a dedicated Replit deployment runbook with required env vars, migration flow, rollback procedure, and operational checks (`docs/replit-deployment-runbook.md`). |
| OPS-02 | **DONE** | 2026-02-06 | Introduced Python transitive lockfile workflow with `requirements.lock.txt` and `requirements-dev.lock.txt` generated via `uv pip compile`; updated CI/Replit/backend installs to consume lockfiles. |
| OPS-03 | **DONE** | 2026-02-06 | Added Bun cache restore/save in CI for `~/.bun/install/cache` in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`. |
| OPS-04 | **DONE** | 2026-02-06 | Removed unnecessary `needs: backend-lint` from `backend-test` in `.github/workflows/ci.yml` to shorten CI critical path. |
| OPS-05 | **DONE (DE-SCOPED)** | 2026-02-06 | Docker compose workflow finding archived because Docker compose manifests are no longer active in this repository. |
| OPS-06 | **DONE (DE-SCOPED)** | 2026-02-06 | Docker service health-check finding archived because Docker compose manifests are no longer active in this repository. |
| OPS-07 | **DONE** | 2026-02-06 | Added generated-file staleness CI guard in `.github/workflows/data-sync-check.yml` to prevent Python/TypeScript data drift. |
| OPS-08 | **DONE (DE-SCOPED)** | 2026-02-06 | Dev/prod compose split finding archived because Docker compose manifests are no longer active in this repository. |
| OBS-01 | **DONE** | 2026-02-06 | Added low-overhead backend observability baseline: structured JSON request logs, API `x-request-id` propagation, route-grouped request metrics, and middleware wiring/tests (`backend/app/core/observability.py`, `backend/app/main.py`, `tests/test_middleware.py`). |
| OBS-02 | **DONE** | 2026-02-06 | Added sampled tracing + alerting workflow for Replit deployments: OpenTelemetry trace sampling/export (OTLP or stdout), `x-trace-id` propagation, threshold-based `http.alert` events with optional webhook dispatch, new runtime settings, and middleware/config/runbook test coverage (`backend/app/core/observability.py`, `backend/app/core/config.py`, `tests/test_middleware.py`, `tests/test_config.py`, `docs/replit-deployment-runbook.md`). |
| BE-01 | **DONE** | 2026-02-06 | Replaced request-size middleware with ASGI-level pre-handler enforcement for `Content-Length` and chunked bodies; added tests preventing side effects on oversized requests (`backend/app/core/middleware.py`, `tests/test_middleware.py`). |
| BE-02 | **DONE** | 2026-02-06 | Refactored session response assembly to avoid double-fetch/refresh and use eager-loaded related records (`backend/app/services/sessions.py`). |
| BE-03 | **DONE** | 2026-02-06 | Reworked BEV-vs-diesel analytics from per-pair query loop to a single aggregate query (`backend/app/services/sessions.py`). |
| BE-04 | **DONE** | 2026-02-06 | Standardized scenario identifiers to canonical keys, preserved UI label display, and added migration backfill (`shared/calculator/tcoCalculator.ts`, `backend/app/services/sessions.py`, `backend/alembic/versions/20260206_000005_005_normalize_scenario_keys.py`, `frontend/src/utils/scenario.ts`). |
| BE-05 | **DONE** | 2026-02-06 | Fixed offline migration SQL output file-handle leak with a context manager (`backend/app/db/session.py`). |
| SEC-01 | **DONE (DE-SCOPED)** | 2026-02-06 | Docker hardening item is N/A for current Replit-managed deployment; no active Dockerfiles in repo. |
| SEC-02 | **DONE (DE-SCOPED)** | 2026-02-06 | `.dockerignore` item is N/A while Docker build contexts are not in active use. |
| SEC-03 | **DONE** | 2026-02-06 | Completed session-secret hashing migration to prefixed SHA-256 and removed bcrypt runtime dependency (`backend/app/core/security.py`, `requirements.txt`). |
| SEC-04 | **DONE** | 2026-02-06 | Replaced `allowedHosts: true` with an explicit allowlist and env override in Vite (`frontend/vite.config.ts`). |
| SEC-05 | **DONE** | 2026-02-06 | Narrowed cache exception handling to `RedisError` and added targeted cache tests to ensure programming errors are not silently swallowed (`backend/app/core/cache.py`, `tests/test_cache.py`). |
| SEC-06 | **DONE** | 2026-02-06 | Removed session secret from JSON create responses; session auth is now cookie-only (`backend/app/models/session.py`, `backend/app/api/router.py`, `shared/types/tco.types.ts`, frontend session client code). |
| SEC-07 | **DONE** | 2026-02-06 | Removed user-input echo from UUID validation error response (`backend/app/api/router.py`). |
| SEC-08 | **DONE** | 2026-02-06 | Resolved event-loop blocking risk by removing bcrypt verification path and dead compatibility code; SHA-256 verification is now lightweight (`backend/app/core/security.py`, `tests/test_security.py`). |
