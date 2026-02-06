# Codebase Audit and Refactor Plan

**Date:** 2026-02-06
**Auditor:** Claude Opus 4.5 (automated, multi-agent)
**Scope:** Full monorepo: backend, frontend, shared calculator, data layer, infrastructure

---

## 1. Executive Summary

This audit identified **86 findings** across the TCO Web Platform (75 from automated multi-agent analysis, 11 additional from a targeted follow-up review). The codebase is in reasonable shape for an early-stage product built with AI assistance. Linting, formatting, and dependency vulnerability scans all pass. The shared calculator engine has strong test coverage and Python-TypeScript parity verification.

**What matters most:**

1. **Test infrastructure and coverage still need work.** Component-test enablement, CI type checks, and E2E execution in CI remain incomplete.

2. **Deployment and observability guidance is still thin.** There is no formal production runbook for Replit deployment and no structured telemetry stack for request-level troubleshooting.

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
| Test coverage and CI safety rails | **Medium** | Core parity/unit suites are strong, but CI type checking and E2E CI coverage remain incomplete. |
| Deployment and operations | **Medium** | Replit deployment documentation and observability baselines remain incomplete. |
| Code maintainability | **Low-Medium** | Major duplication/dead-code cleanup is complete; targeted AI-pattern refactors remain. |

---

## 4. Findings

Sections `4.1`, `4.3`, `4.4`, and `4.5` are complete and have been moved to Section 10 (`DONE`) at the bottom of this document.

### 4.2 Security & Privacy

Security items `SEC-01` through `SEC-08` are complete (or explicitly de-scoped) and are tracked in Section 10 (`DONE`) at the bottom of this document.

#### SEC-05: Broad `except Exception` in cache module masks programming errors — **RESOLVED**
- **Status (2026-02-06): DONE.** Cache error handling is narrowed to `RedisError` and no longer swallows non-Redis/programming failures.
- **Resolution (2026-02-06):** Updated `backend/app/core/cache.py` to catch `RedisError` only for Redis I/O paths and added focused coverage in `tests/test_cache.py` for serialization/JSON error propagation and Redis failure fallback behavior.

### 4.6 Dependency Health

Dependency items `DEP-01` through `DEP-07` are complete and have been moved to Section 10 (`DONE`) at the bottom of this document.

#### DEP-05: CI uses `bun install` without `--frozen-lockfile` — **RESOLVED**
- **Status (2026-02-06): DONE.** Added `--frozen-lockfile` to CI Bun installs in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`.
- **Original impact:** CI could resolve different dependency versions than lockfile specifies.

#### DEP-06: `BUN_VERSION: 'latest'` in CI — **RESOLVED**
- **Status (2026-02-06): DONE.** Pinned CI Bun runtime to `1.3.5` in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`.
- **Original impact:** Frontend builds were not reproducible.

#### DEP-07: No automated dependency update workflow — **RESOLVED**
- **Status (2026-02-06): DONE.** Added `.github/dependabot.yml` to automate dependency updates:
  - Monthly cadence for runtime version updates (pip + npm + GitHub Actions).
  - Security updates grouped separately via Dependabot `applies-to: security-updates`.
- **Original impact:** Security patches could be missed and upgrades could become high-risk batch changes.

### 4.7 Tests & Observability

Test items `TEST-01` through `TEST-11` are complete and have been moved to Section 10 (`DONE`) at the bottom of this document.

#### OBS-01: No observability instrumentation
- **Evidence:** No OpenTelemetry, Prometheus, or Sentry integration found in backend or frontend code. No structured logging beyond Python's default logger.
- **Impact:** Harder to diagnose performance regressions or failures in production. No request-level tracing for debugging multi-service interactions.
- **Recommendation:** Start with structured logging and request metrics on key paths (session create/update, calculation). Add distributed tracing later as deployment matures.

### 4.8 Build/Deploy Ergonomics

#### OPS-01: No documented Replit deployment runbook
- **Evidence:** Replit deployment config exists in `.replit`, but no dedicated deployment runbook exists under `docs/`.
- **Impact:** Operational setup and rollback steps remain tribal knowledge.
- **Recommendation:** Document the Replit deployment process (env vars, DB migration flow, rollback path, and operational checks).

#### OPS-02: No Python lockfile for transitive dependencies — **RESOLVED**
- **Status (2026-02-06): DONE.** Added lockfile-based Python dependency workflow using `uv pip compile`.
- **Resolution (2026-02-06):** Added `requirements.lock.txt` and `requirements-dev.lock.txt`, updated install paths in `.github/workflows/ci.yml`, `.github/workflows/data-sync-check.yml`, `.github/workflows/dependency-audit.yml`, `.replit`, and `backend/requirements.txt`, and documented lockfile regeneration in `README.md`.
- **Original impact:** Transitive deps could change between installs.

#### OPS-03: No bun cache in CI — **RESOLVED**
- **Status (2026-02-06): DONE.** Added Bun install-cache restore/save in CI.
- **Resolution (2026-02-06):** Added `actions/cache` entries for `~/.bun/install/cache` in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`.
- **Original impact:** Every frontend CI job installed dependencies from scratch.

#### OPS-04: Backend test job depends on lint job unnecessarily — **RESOLVED**
- **Status (2026-02-06): DONE.** Removed backend test dependence on lint.
- **Resolution (2026-02-06):** Removed `needs: backend-lint` from `backend-test` in `.github/workflows/ci.yml` so lint and tests run in parallel while `ci-success` still gates on both.
- **Original impact:** Lint runtime was added to CI critical path.

#### OPS-05: Docker compose `env_file` fails on fresh clone — **DE-SCOPED**
- **Status (2026-02-06): DONE (DE-SCOPED).** Docker compose files are no longer active in this repository.
- **Original impact:** `docker compose up` failed after fresh clone due to required local env file.

#### OPS-06: No health checks on Docker services — **DE-SCOPED**
- **Status (2026-02-06): DONE (DE-SCOPED).** Docker compose files are no longer active in this repository.
- **Original impact:** Backend startup ordering was vulnerable to dependency readiness races.

#### OPS-07: No automated staleness check for generated TypeScript files — **RESOLVED**
- **Evidence:** Generation script must be run manually. No CI enforcement.
- **Impact:** Python and TypeScript data layers can silently diverge.
- **Recommendation:** Add CI step that regenerates and checks for uncommitted diffs.
- **Resolution (2026-02-06):** Already implemented. `.github/workflows/data-sync-check.yml` runs the generation script and checks for uncommitted diffs.

#### OPS-08: Single Docker Compose file serves dev and production — **DE-SCOPED**
- **Status (2026-02-06): DONE (DE-SCOPED).** Docker compose files are no longer active in this repository.
- **Original impact:** Risk of shipping dev server settings in production container workflows.

### 4.9 AI-Generated Code Patterns

#### AI-01: Repetitive sanitization code in `tcoCalculator.ts`
- **Evidence:** `tcoCalculator.ts:126-267`. Each of 16 override fields gets its own 5-6 line block with identical pattern. ~140 lines of repetitive code.
- **Impact:** Adding a new override requires copying a block exactly. Brittle.
- **Recommendation:** Refactor to iterate over `OVERRIDE_LIMITS` dynamically. Reduces to ~20 lines.
- **Refactor warning (2026-02-06):** `annual_kms_variation` uses `clampOverrideAboveMin()` (rejects sub-minimum values) while all other overrides use `clampOverrideValue()` (clamps to range). Any data-driven refactor must preserve this distinction or the two clamping behaviours will be silently unified.

#### AI-02: Overly defensive null checks on guaranteed types
- **Evidence:** `WizardDieselStep.tsx:16` uses `(catalog ?? [])` when `useVehicleCatalog` always returns array. `wizardData.overrides ?? {}` in 5+ locations despite `defaultWizardData` initializing it.
- **Impact:** Masks potential bugs. If `overrides` is unexpectedly `undefined`, the `?? {}` silently creates an empty object instead of surfacing the issue.
- **Recommendation:** Trust the type system. Remove unnecessary fallbacks.

#### AI-03: Verbose comments restating code
- **Evidence:** Throughout. `// Determine the winner (lowest cost per km)` before `Math.min(...)`. `// Debounced form-to-store sync` before debounced sync code.
- **Impact:** Clutter. Maintenance burden when code changes but comments don't.
- **Recommendation:** Keep "why" comments, remove "what" comments.

#### AI-04: Audit reference codes as code comments
- **Evidence:** `SEC-004`, `API-002`, etc. in docstrings across most backend files.
- **Impact:** Read like AI-generated checklist artifacts. See DEAD-05.

#### AI-05: `# pragma: no cover` on reachable error branches
- **Evidence:** `router.py:91,116,146,173` and `vehicles.py:23`. These are real error paths that should be tested.
- **Impact:** Suppresses coverage for important error handling code.
- **Recommendation:** Remove pragmas. Write explicit tests for error paths.

#### AI-06: `stableStringify` re-implements a common library pattern
- **Evidence:** `useCalculations.ts:13-29`. Hand-rolled deterministic JSON stringify. Maps both `undefined` and `null` to `'null'`.
- **Impact:** Fragile edge cases. `undefined` vs `null` conflation could cause dedup failures.
- **Recommendation:** Use `fast-json-stable-stringify` or document intentional conflation.

#### AI-07: Frontend silently swallows persist/calculation errors
- **Evidence:** `frontend/src/hooks/useCalculations.ts:47`, `frontend/src/services/sessionLifecycle.ts:46`. Errors caught and logged to console without user notification or recovery path.
- **Impact:** Users may believe state was saved when it wasn't. Silent failures leave the UI in an inconsistent state with no indication anything went wrong.
- **Recommendation:** Surface errors via toast notifications (react-hot-toast is already a dependency). Add retry strategy for transient failures. Pairs well with FE-01 (Error Boundary).

### 4.10 Accessibility

#### A11Y-01: Color contrast failure for muted text
- **Evidence:** `tailwind.config.js:13`. `brand-muted` (#666666) on `brand-background` (#F4F4F3) gives ~3.9:1 contrast ratio, below WCAG AA 4.5:1 requirement.
- **Recommendation:** Darken to at least `#595959`.

#### A11Y-02: Vehicle chips use `div role="button"` instead of `<button>`
- **Evidence:** `WizardElectricStep.tsx:126-162`.
- **Impact:** Custom keyboard handling duplicates native button behavior.
- **Recommendation:** Replace with `<button>` element.

---

## 5. Prioritized Backlog

| ID | Title | Impact | Effort | Risk | Phase | Dependencies |
|----|-------|--------|--------|------|-------|-------------|
| AI-01 | Refactor repetitive sanitization to data-driven (preserve `clampOverrideAboveMin` special case for `annual_kms_variation`) | **Med** | M | Low | 2 | Test coverage first |
| AI-07 | Surface frontend persist errors to users | **Med** | S | Low | 2 | None (FE-01 complete) |
| A11Y-01 | Add chart text alternatives | **Low** | M | Low | 3 | None |
| A11Y-02 | Replace chip pseudo-buttons with `<button>` | **Low** | S | Low | 3 | None |
| OPS-01 | Document Replit deployment process | **Low** | S | Low | 3 | None |
| OBS-01 | Add structured logging (Replit-compatible) | **Low** | M | Low | 3 | None |

*Size: XS=<1hr, S=1-4hr, M=4-16hr, L=16hr+*

---

## 6. Migration Plan

### Phase 1: Safety Rails (1-2 days)

**Goal:** Fix broken infrastructure and add guardrails. All changes are additive or fix-only. Zero functional changes.

Completed and moved to `DONE`:
1. MAINT-01 (pin ruff version consistently)
2. MAINT-03 (add missing test dependencies to `requirements-dev.txt`)
3. MAINT-07 (add `react-hooks/recommended` to ESLint extends)
4. DEP-05 (enforce `bun install --frozen-lockfile` in CI)
5. DEP-06 (pin Bun version in CI)

Remaining:
1. None. Phase 1 items are complete.

**Rollback:** All changes are independent. Any can be reverted individually.
**Verification:** CI passes. `bun test` passes. `pytest tests/` passes locally.

### Phase 2: Low-Risk Refactors (3-5 days)

**Goal:** Fix calculation accuracy issues, improve test coverage, clean up dead code. Each change is well-tested and reversible.

**Calculator accuracy fixes (remaining):**

Completed and moved to `DONE`:
1. CALC-01 (annuity-due formula)
2. CALC-02 (articulated BEV charging mix)
3. CALC-03 (fuel tax credit)
4. CALC-04 (road user charge handling)
5. CALC-05 (rebate parity alignment)
6. CALC-06 (grouped cost breakdown migration)
7. CALC-07 (battery replacement year constant)
8. CALC-08 (remove misleading vehicle maintenance field)
9. TEST-04/TEST-05 (expanded verification fixtures and override cases)

Remaining:
1. None. Calculator accuracy items are complete.

**Test and CI improvements:**

1. Surface frontend persist/calculation errors to users (`AI-07`)

**Cleanup and maintenance:**

Completed and moved to `DONE`:
1. DEAD-01, DEAD-02, and DEAD-04 through DEAD-07 (dead-code/dependency cleanup)
2. DEP-07 (Dependabot automation for dependency updates)
3. SEC-05 (narrow cache exception handling)
4. OPS-02 (Python transitive lockfile workflow)
5. OPS-03 (Bun cache in CI)
6. OPS-04 (remove backend lint->test CI coupling)

Remaining:
1. Refactor repetitive sanitization to data-driven

**Rollback:** Each item is a separate PR. Revert any single PR if issues arise.
**Verification:** Full CI pass. Calculator parity tests pass with updated verification data. Coverage increases.

### Phase 3: Structural Improvements (ongoing)

**Goal:** Larger improvements that require more coordination. Execute as capacity allows.

1. Add component tests using React Testing Library
2. Add accessibility improvements (charts, stepper, error messages)
3. Document Replit deployment process
4. Add structured logging (Replit-compatible)

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

### Fix existing CI checks

| Issue | Fix |
|-------|-----|
| Ruff version drift | **DONE:** pinned to `ruff==0.8.0` in CI and `requirements-dev.txt` |
| BUN_VERSION: latest | **DONE:** pinned to `1.3.5` in CI workflows |
| Missing frozen lockfile | **DONE:** `bun install --frozen-lockfile` applied to CI install steps |
| No Python transitive lockfile | **DONE:** Added `requirements.lock.txt` and `requirements-dev.lock.txt` via `uv pip compile`; CI/Replit now install from lockfiles |
| Sequential backend jobs | **DONE:** Removed `needs: backend-lint` from `backend-test` |
| No bun cache | **DONE:** Added `actions/cache` for `~/.bun/install/cache` in CI workflows |
| Vitest includes e2e | **DONE:** `e2e/` excluded from Vitest glob |

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

### Deferred Items (excluded from phased plan)

None currently.

### Assumptions (verified or updated)

- **Deployment target:** Replit with Replit-managed database. **Confirmed.** Docker hardening items are dev-environment-only improvements.
- **User base scale:** Recommendations assume moderate traffic (tens to low hundreds of concurrent users). Current implementation uses SHA-256 session-secret verification and avoids previous bcrypt CPU overhead in request paths.
- **PostgreSQL version:** Replit-managed PostgreSQL version may vary by environment; no active Docker-compose pin exists in this repository.
- **Browser support:** No browserslist config found beyond the env var workaround. Assumed modern browsers (Chrome/Firefox/Safari/Edge latest 2 versions).
- **Session secret migration:** Completed. Session secret is cookie-only and not returned in JSON responses.
- **Analytics performance targets:** No SLOs for analytics endpoints found. BE-03 was implemented with a single aggregate query; revisit only if business-level analytics SLOs are introduced.
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

### Audit Sources

This audit consolidates two reviews:

1. **Multi-agent automated analysis (2026-02-06):** 5 parallel agents covering backend, frontend, shared calculator, health checks, and infrastructure. Produced the original 75 findings.
2. **Targeted follow-up review (2026-02-06):** Focused review of middleware, session security, validation consistency, and dead code. Added 11 findings (BE-04, BE-05, SEC-08, MAINT-11, MAINT-12, DEAD-06, DEAD-07, DEP-07, OBS-01, OPS-08, AI-07) and enriched BE-01 with side-effects detail.

### Agent Reports

This audit was conducted using 5 parallel analysis agents:

1. **Backend review** (ad95a15): 62 tools, ~87K tokens. Reviewed all backend code, tests, services, models, middleware, security.
2. **Frontend review** (a8ae621): 71 tools, ~103K tokens. Reviewed all frontend components, hooks, state, services, tests, config.
3. **Shared calculator review** (a2879fa): 42 tools, ~97K tokens. Reviewed calculator engine, math utilities, types, data layer, generation scripts, verification data.
4. **Health checks** (adaac0f): 13 commands run. Ruff, black, isort, pytest, typecheck, eslint, vitest, bandit, pip-audit, vulture, mypy.
5. **Infrastructure review** (a20c980): 120+ tools, ~57K tokens. Reviewed CI, Docker, dependencies, config, migrations, deployment.

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
| OPS-02 | **DONE** | 2026-02-06 | Introduced Python transitive lockfile workflow with `requirements.lock.txt` and `requirements-dev.lock.txt` generated via `uv pip compile`; updated CI/Replit/backend installs to consume lockfiles. |
| OPS-03 | **DONE** | 2026-02-06 | Added Bun cache restore/save in CI for `~/.bun/install/cache` in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`. |
| OPS-04 | **DONE** | 2026-02-06 | Removed unnecessary `needs: backend-lint` from `backend-test` in `.github/workflows/ci.yml` to shorten CI critical path. |
| OPS-05 | **DONE (DE-SCOPED)** | 2026-02-06 | Docker compose workflow finding archived because Docker compose manifests are no longer active in this repository. |
| OPS-06 | **DONE (DE-SCOPED)** | 2026-02-06 | Docker service health-check finding archived because Docker compose manifests are no longer active in this repository. |
| OPS-07 | **DONE** | 2026-02-06 | Added generated-file staleness CI guard in `.github/workflows/data-sync-check.yml` to prevent Python/TypeScript data drift. |
| OPS-08 | **DONE (DE-SCOPED)** | 2026-02-06 | Dev/prod compose split finding archived because Docker compose manifests are no longer active in this repository. |
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
