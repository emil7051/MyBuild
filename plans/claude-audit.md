# Codebase Audit and Refactor Plan

**Date:** 2026-02-06
**Auditor:** Claude Opus 4.5 (automated, multi-agent)
**Scope:** Full monorepo: backend, frontend, shared calculator, data layer, infrastructure

---

## 1. Executive Summary

This audit identified **86 findings** across the TCO Web Platform (75 from automated multi-agent analysis, 11 additional from a targeted follow-up review). The codebase is in reasonable shape for an early-stage product built with AI assistance. Linting, formatting, and dependency vulnerability scans all pass. The shared calculator engine has strong test coverage and Python-TypeScript parity verification.

**What matters most:**

1. **Calculator accuracy risks (HIGH).** The annualised cost formula uses an ordinary annuity instead of annuity-due, inflating the displayed annual cost and cost-per-km by ~5%. The articulated BEV charging mix sums to 0.90 instead of 1.0, reducing fuel costs by ~10% for that weight class. The fuel tax credit ($0.203/L) is defined but never applied, potentially overstating diesel costs by ~10%. These affect the numbers users see when making purchasing decisions.

2. **Test infrastructure is broken.** Backend tests cannot run locally (pytest-asyncio incompatibility). ~~Two frontend tests fail (Playwright spec loaded by Vitest, `vi.resetModules` issue).~~ *Resolved: 142/142 Vitest tests now pass.* Vitest uses `node` environment, blocking all component testing. Zero React component tests exist.

3. **CI gaps leave real risks undetected.** No mypy type checking, no E2E tests, no SAST scanning, no Prettier enforcement. Ruff version drift between local and CI. Bun version not pinned. Frontend lockfile not frozen in CI.

4. **Docker and deployment need hardening.** No `.dockerignore`, no multi-stage builds, containers run as root, no health checks, no production Dockerfile or deployment pipeline. Heavy unused Python dependencies (numpy, pandas, plotly) inflate the backend image.

5. **AI-generated code patterns** are present but manageable. Repetitive sanitization code, defensive null checks on guaranteed types, verbose comments restating code, audit-reference comments throughout. These add maintenance burden but don't introduce bugs.

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

**Backend:** FastAPI 0.128 + SQLAlchemy 2.0.25 + Alembic 1.13 + asyncpg + Redis 5.0 + bcrypt + slowapi
**Frontend:** React 18 + React Query 5 + Zustand 4 + React Hook Form 7 + Zod 3 + Recharts 2 + Vite 7 + Vitest 4
**Shared:** Pure TypeScript, no external deps

---

## 3. Top Risks & Hotspots

Ranked by likelihood x impact. Scores: L=likelihood (1-5), I=impact (1-5), Risk=LxI.

| # | Risk | L | I | Risk | Category |
|---|------|---|---|------|----------|
| 1 | Annualised cost formula inflates displayed annual cost by ~5% | 5 | 5 | **25** | Calculator correctness |
| 2 | Articulated BEV charging mix sums to 0.90, not 1.0 | 5 | 4 | **20** | Data integrity |
| 3 | Fuel tax credit defined but not applied (diesel costs overstated ~10%) | 4 | 5 | **20** | Calculator completeness |
| 4 | Backend tests cannot run locally (pytest-asyncio incompatibility) | 5 | 4 | **20** | Test infrastructure |
| 5 | Zero React component tests; Vitest env blocks component testing | 5 | 3 | **15** | Test coverage |
| 6 | No mypy in CI; type errors in async Python code undetected | 4 | 3 | **12** | CI gaps |
| 7 | Ruff version drift between local (0.0.290) and CI (latest) | 4 | 3 | **12** | CI reproducibility |
| 8 | Python/TypeScript rebate calculation logic diverges (dormant) | 2 | 5 | **10** | Cross-language parity |
| 9 | No `.dockerignore`; backend image contains tests, .git, archive | 4 | 2 | **8** | Docker |

**Update (2026-02-06):** CALC-01, CALC-02, CALC-03, and CALC-04 have been completed and moved to the `DONE` section.

---

## 4. Findings

### 4.1 Correctness & Reliability

#### CALC-01: `calculateAnnualisedCost` uses ordinary annuity instead of annuity-due
- **Status (2026-02-06): DONE.** Updated to annuity-due annualisation and regenerated verification fixtures.
- **Original evidence:** `shared/calculator/math.ts:69-85`. Uses `(totalNPV * r) / (1 - (1+r)^-n)` (payment at end of period). For a TCO tool where costs are incurred throughout each year, annuity-due `* (1+r)` is more accurate.
- **Impact:** Inflates displayed `annual_cost` and `cost_per_km` by ~5% (one discount rate period). This is the primary comparison metric shown to users.
- **Root cause:** Standard annuity formula applied without considering timing convention.
- **Decision:** Fix to annuity-due. Multiply the result by `(1 + r)`.
- **Tradeoffs:** This shifts all displayed annual costs downward by ~5%. Verification data must be regenerated. Need to check whether the Python reference uses the same formula (if so, fix both).
- **Test plan:** Update `verification_data.json` from Python. All parity tests should pass with the new values. Add a unit test comparing the formula output against a known financial calculator result.

#### CALC-02: Articulated BEV charging mix sums to 0.90
- **Status (2026-02-06): DONE.** Fixed articulated BEV charging mix to sum to 1.0 and added validation in `scripts/validation.py`.
- **Original evidence:** `data/constants.py:121-125`. Articulated BEV mix: `{depot_overnight: 0.40, depot_fast: 0.30, public_fast: 0.20}` = 0.90. All other weight classes sum to 1.0. The calculator at `tcoCalculator.ts:588-601` uses the mix as proportional weights for blended electricity cost.
- **Impact:** 10% of articulated BEV charging cost is unaccounted for, systematically undercharging fuel costs for that weight class.
- **Recommendation:** Fix the Python constant (likely `depot_overnight: 0.50` or distribute the missing 0.10). Add a validation check that charging mix sums to 1.0 per weight class.
- **Test plan:** Add assertion in `scripts/validation.py`. Regenerate all downstream files. Parity tests will catch the calculation change.

#### CALC-03: Fuel tax credit defined but never applied
- **Status (2026-02-06): DONE.** Applied fuel tax credit in diesel fuel-cost calculation and regenerated verification fixtures.
- **Original evidence:** `data/constants.py:166-168` defines `FUEL_TAX_CREDIT = 0.203`. Generated to TypeScript at `constants.generated.ts:54`. The calculator never references it. The diesel price is `$2.05/L` which "includes 2c for AdBlue." Heavy vehicle operators in Australia can claim the fuel tax credit ($0.203/L) as a rebate.
- **Impact:** If the credit applies to these operators, effective diesel cost should be `$2.05 - $0.203 = $1.847/L`. Omitting this overstates diesel costs by ~10%, biasing results toward BEVs.
- **Decision:** Apply the fuel tax credit. Subtract $0.203/L from diesel cost in `calculateFuelCostYear`. Effective diesel cost becomes $2.05 - $0.203 = $1.847/L.
- **Test plan:** Regenerate verification data from Python and confirm parity. Add a unit test verifying the credit is applied.

#### CALC-04: Road user charge defined but not applied
- **Status (2026-02-06): DONE.** Implemented BEV road-user-charge as an optional override toggle, defaulting to OFF.
- **Original evidence:** `data/constants.py:169-171` defines `ROAD_USER_CHARGE = 0.305`. Scenario types include `road_user_charge_bev_start_year` and `policy_phase_out_year` (`shared/types/tco.types.ts:31-32`). The calculator ignores all of these.
- **Impact:** Planned feature infrastructure exists but is inactive. Road user charges for BEVs are active Australian policy. Not applying them understates BEV operating costs.
- **Decision:** Implement as opt-in toggle (`apply_road_user_charge_bev`) with default OFF, so current policy settings remain reflected while enabling scenario testing.

#### CALC-05: Python and TypeScript rebate calculation logic diverges
- **Evidence:** TypeScript at `tcoCalculator.ts:694-711` applies fixed rebate before calculating percentage rebate base (`percentageBase = Math.max(0, msrp - rebate)`). Python at `policies.py:163-180` calculates percentage rebate on the full `vehicle_price`.
- **Impact:** No current impact (both policies disabled). If both rebates are enabled simultaneously, the two implementations produce different results.
- **Recommendation:** Align the logic. Most rebate schemes apply to the base price. Update whichever implementation is wrong.

#### CALC-06: Mixed-basis cost breakdown can mislead users
- **Evidence:** `shared/types/tco.types.ts:83-140`. The `CostBreakdown` struct mixes NPV-adjusted values (fuel, maintenance), nominal lifetime totals (insurance, registration), and upfront values (purchase). Returned as a flat object.
- **Impact:** If anyone sums breakdown fields to reconstruct `total_cost`, they get a wrong answer. Chart components stacking these values may present misleading visualizations.
- **Decision:** Restructure into named groups (`npv_costs`, `nominal_costs`, `upfront_costs`). This is a breaking change that touches the calculator output, all chart components, API response shapes, and session storage. Requires a comprehensive migration plan (see Phase 2 sub-plan for CALC-06).

#### CALC-07: `BATTERY_REPLACEMENT_YEAR` not in Python constants
- **Evidence:** `tcoCalculator.ts:318` uses `CONSTANTS.BATTERY_REPLACEMENT_YEAR ?? 8`. Not defined in `data/constants.py` or `constants.generated.ts`. The nullish coalescing silently falls back to 8.
- **Impact:** Hidden magic number outside the generation pipeline.
- **Recommendation:** Add `BATTERY_REPLACEMENT_YEAR = 8` to `data/constants.py`.

#### CALC-08: Vehicle `maintenance_cost_per_km` field ignored by calculator
- **Evidence:** Vehicle catalog has per-vehicle values (BEV001=0.05, DSL001=0.20). Calculator uses per-weight-class constants instead (BEV Light Rigid=0.10, Diesel Light Rigid=0.18). `tcoCalculator.ts:546-553`.
- **Impact:** Users see one maintenance cost in vehicle specs, calculations use a different number. Confusing.
- **Decision:** Use per-weight-class constants (current calculator behavior). Remove the misleading `maintenance_cost_per_km` field from the vehicle catalog data to avoid showing users a number that doesn't drive calculations.

#### FE-01: Missing Error Boundary
- **Evidence:** No `ErrorBoundary` component in `frontend/src/`. No `componentDidCatch` or `getDerivedStateFromError` usage. Searched entire `src/`.
- **Impact:** Any React rendering error crashes the entire app with a white screen. No recovery path.
- **Recommendation:** Add a top-level error boundary with a user-friendly fallback UI and retry mechanism.

#### FE-02: `VehicleParamsForm` validation bypasses React Hook Form
- **Evidence:** `VehicleParamsForm.tsx:28-83` uses its own `useState<FieldErrors>` and manual Zod validation instead of integrating with the React Hook Form context.
- **Impact:** The wizard "Next" button validation doesn't check vehicle parameter overrides. Users can proceed with invalid overrides.
- **Recommendation:** Integrate vehicle param overrides into the React Hook Form schema.
- **Codex verification note (2026-02-06):** Field-level Zod `safeParse` at `VehicleParamsForm.tsx:52` prevents invalid overrides from entering state. The bypass concern is an architecture consistency issue (parallel validation systems), not a user-facing correctness bug. Downgraded from risk table accordingly.

#### FE-03: PaybackChart uses simplified linear interpolation on NPV data
- **Evidence:** `PaybackChart.tsx:18-50`. Calculates payback by dividing `total_cost` by `VEHICLE_LIFE` to get a per-year cost rate. This assumes costs are evenly distributed, but early years have higher financing costs and later years have battery replacement.
- **Impact:** Payback year displayed could be materially inaccurate for users making purchasing decisions.
- **Decision:** Compute year-by-year nominal cash flows for accurate payback period. The calculator already computes per-year values internally, so the data is available.

#### BE-01: Request size middleware allows side effects before rejection
- **Evidence:** `backend/app/core/middleware.py:24,66,68,72`. The middleware calls `call_next` before checking `size_exceeded`, so handlers can run and commit side effects on partial/truncated bodies before the 413 is returned. For chunked requests without `Content-Length`, the header-based size check is bypassed entirely. The implementation also relies on a private `request._receive` override that could break on ASGI framework upgrades.
- **Impact:** Oversized or malicious payloads can trigger partial writes or inconsistent state. Chunked requests can bypass the size check entirely.
- **Decision:** Deferred. The risk is low given the app's threat model (small JSON payloads for a TCO calculator). See "Deferred Items" in Section 8. Questions to resolve: What is the actual threat model at current scale? Does Replit's infrastructure provide any upstream request size limits? Is the partial-write risk real given the current endpoint behavior?

#### BE-02: `_build_response` double-fetches session records
- **Evidence:** `backend/app/services/sessions.py:290-330`. Calls `db.get()` then `db.refresh()` (two DB round trips), then makes separate queries for operator profile and feedback. Total: 4-5 queries per response.
- **Impact:** Each session read/update involves multiple unnecessary database round trips.
- **Recommendation:** Pass the already-loaded record. Use eager loading (`selectinload`/`joinedload`) for related records.

#### BE-03: Analytics executes N queries per BEV-diesel pair
- **Evidence:** `backend/app/services/sessions.py:244-280`. Loop executes one query per BEV-diesel comparison pair. With 8 BEV vehicles, that is 8 queries per analytics call.
- **Impact:** At least 12 queries per analytics summary call.
- **Recommendation:** Rewrite as a single query with `UNION ALL` or conditional aggregation.

#### BE-04: Scenario identifier drift in stored results
- **Evidence:** `shared/types/tco.types.ts:74`, `shared/calculator/tcoCalculator.ts:899`, `backend/app/services/sessions.py:395`. Calculator returns `scenario.name` (display label) in results. Request payloads and other parts of the system use scenario keys.
- **Impact:** Stored results contain mixed identifiers, complicating analytics filters, data exports, or future migrations that assume a consistent key.
- **Recommendation:** Store both `scenario_key` and `scenario_label`, or change calculator to return the key and derive the label in the UI. If changing stored values, backfill existing rows or version the API.

#### BE-05: File handle leak in offline migration generator
- **Evidence:** `backend/app/db/session.py:81-92`. `run_migrations_offline` opens a file with `open(output_file, "w")` but never closes it (no context manager or explicit `close()`).
- **Impact:** Minor resource leak in CLI tooling. Could matter in long-lived processes or repeated invocations.
- **Recommendation:** Wrap with `with open(...) as f:` context manager.

### 4.2 Security & Privacy

#### SEC-01: Docker containers run as root
- **Evidence:** Neither `backend/Dockerfile` nor `frontend/Dockerfile` contains a `USER` directive.
- **Impact:** Container compromise gives root privileges. Production security concern.
- **Recommendation:** Add non-root user directives to both Dockerfiles.

#### SEC-02: No `.dockerignore` files
- **Evidence:** No `.dockerignore` files exist anywhere in the project.
- **Impact:** Backend image includes tests, `.git`, archive, `.env` files. Attack surface and image bloat.
- **Recommendation:** Create `.dockerignore` in project root and `frontend/`.

#### SEC-03: bcrypt 12 rounds excessive for high-entropy session secrets
- **Evidence:** `backend/app/core/security.py:132`. Session secrets are 256-bit random tokens (not user-chosen passwords).
- **Impact:** Each session create/verify adds ~250ms of bcrypt overhead. Unnecessary for high-entropy tokens.
- **Recommendation:** Consider HMAC-SHA256 for session secret hashing, or reduce to 10 rounds.

#### SEC-04: `vite.config.ts` sets `allowedHosts: true`
- **Evidence:** `frontend/vite.config.ts:26`.
- **Impact:** Disables Vite host header validation. Enables DNS rebinding attacks in development.
- **Recommendation:** Change to `allowedHosts: ['localhost', '127.0.0.1']`.

#### SEC-05: Broad `except Exception` in cache module masks programming errors
- **Evidence:** `backend/app/core/cache.py:58,83,111`. All Redis operations catch `Exception` broadly.
- **Impact:** A bug in cache serialization (e.g., `json.dumps` failure) is silently treated as a Redis connection issue.
- **Recommendation:** Catch `redis.RedisError` specifically. Let programming errors propagate.

#### SEC-06: Session secret echoed in both JSON body and HttpOnly cookie
- **Evidence:** `backend/app/api/router.py:112-117`.
- **Impact:** The JSON body is visible in dev tools and proxy logs. The cookie alone would suffice for browser re-submission.
- **Decision:** Deferred. Needs further investigation before deciding. See "Deferred Items" in Section 8. Questions to resolve: Are there non-browser API consumers? Is the cookie migration complete? What breaks if JSON body is removed?

#### SEC-07: Error response echoes user input
- **Evidence:** `backend/app/api/router.py:69`. Error message includes the invalid `session_id`.
- **Impact:** Low XSS risk since it is a JSON API, but poor practice.
- **Recommendation:** Remove echoed input: `"Invalid session_id format. Expected a valid UUID v4."`

#### SEC-08: bcrypt blocks the async event loop
- **Evidence:** `backend/app/core/security.py:123,136`, `backend/app/services/sessions.py:46,98`. Synchronous bcrypt hash/verify called directly inside async request handlers.
- **Impact:** CPU-bound hashing (~250ms per operation at 12 rounds) blocks the event loop under load, causing latency spikes across all concurrent requests. Potential DoS amplification vector.
- **Recommendation:** Offload bcrypt operations to a worker thread via `anyio.to_thread.run_sync`. Alternatively, reduce rounds per SEC-03 (high-entropy secrets don't need 12 rounds) or switch to HMAC-SHA256 for session secrets.

### 4.3 Performance

#### PERF-01: No frontend code splitting
- **Evidence:** `frontend/src/App.tsx:1-16`. No `React.lazy()` or dynamic imports. `chunkSizeWarningLimit` raised to 900KB in `vite.config.ts:21`.
- **Impact:** Entire app (including Recharts for 5 chart components) loaded on initial page load.
- **Recommendation:** Lazy-load `ResultsPage` and chart components.

#### PERF-02: `Intl.NumberFormat` instantiated on every render
- **Evidence:** `frontend/src/utils/format.ts:7-24`. `formatCurrency` and `formatCurrencyCompact` create new instances per call.
- **Impact:** `Intl.NumberFormat` construction involves locale resolution. Called dozens of times in chart components.
- **Recommendation:** Cache instances by options signature.

#### PERF-03: Six chart components each subscribe to full Zustand store
- **Evidence:** All chart components in `frontend/src/components/results/` independently subscribe to `state.results`.
- **Impact:** A single results update triggers six re-renders, each with non-trivial data transformation.
- **Recommendation:** Memoize chart data transformations with `useMemo`, or lift data preparation to a single parent.

#### PERF-04: Docker backend installs heavy unused Python packages
- **Evidence:** `requirements.txt` includes numpy (25MB), pandas (60MB), plotly (30MB) used only in archived code.
- **Impact:** Backend Docker image bloat (~115MB of unused libraries).
- **Recommendation:** Move to a separate `requirements-scripts.txt`.

### 4.4 Maintainability

#### MAINT-01: Ruff version drift between local and CI
- **Evidence:** `requirements-dev.txt:12` pins `ruff==0.0.290`. CI at `ci.yml:34` installs `ruff` unpinned (gets latest 0.8.x+). The `0.0.x` series had different rule defaults.
- **Impact:** Code can pass CI but fail locally, or vice versa.
- **Recommendation:** Pin ruff to the same modern version everywhere.

#### MAINT-02: Three overlapping Python linting ecosystems
- **Evidence:** `requirements-dev.txt` includes ruff, flake8 (+3 plugins), and pylint. CI only runs ruff.
- **Impact:** Confusing for developers. Wasted install time. Modern ruff subsumes flake8 + many pylint rules.
- **Recommendation:** Consolidate on ruff. Remove flake8, flake8 plugins, and pylint.

#### MAINT-03: Test dependencies missing from `requirements-dev.txt`
- **Evidence:** CI installs `httpx` and `factory-boy` inline (`ci.yml:63`). Neither in `requirements-dev.txt`. Also `anyio`/`pytest-anyio` not listed but tests use `@pytest.mark.anyio`.
- **Impact:** `pip install -r requirements-dev.txt && pytest` fails for developers.
- **Recommendation:** Add `httpx`, `factory-boy`, and `anyio` to `requirements-dev.txt`.

#### MAINT-04: `constants.future.ts` duplicates generated constants
- **Evidence:** Every value in `FUTURE_CONSTANTS` also exists in `constants.generated.ts` with the same value.
- **Impact:** If Python constants change, the generated file updates but `constants.future.ts` stays stale.
- **Recommendation:** Remove duplicates from `constants.future.ts`.

#### MAINT-05: Dead frontend component `WizardVehicleStep`
- **Evidence:** `WizardVehicleStep.tsx` is not imported anywhere. Superseded by `WizardDieselStep` and `WizardElectricStep`.
- **Impact:** Dead code.
- **Recommendation:** Delete the file.

#### MAINT-06: Duplicate payload-building logic in 3 locations
- **Evidence:** `WizardCompareStep.tsx:15-53`, `AppShell.tsx:22-42`, and `payload.ts` utilities. Subtle differences exist (e.g., deduplication approach).
- **Impact:** Payload shape change requires updating 3 locations.
- **Recommendation:** Extract a single `buildComparisonPayload(wizardData)` utility.

#### MAINT-07: ESLint missing `react-hooks/recommended`
- **Evidence:** `.eslintrc.cjs:12` includes `'react-hooks'` in plugins but `extends` does not include `'plugin:react-hooks/recommended'`.
- **Impact:** React hooks rules (exhaustive deps, rules of hooks) not enforced. Stale closure bugs go undetected.
- **Recommendation:** Add to `extends` array.

#### MAINT-08: `ConstantCatalog` provides no compile-time type safety
- **Evidence:** `shared/types/tco.types.ts:13-15`. Typed as `Record<string, NestedValue>`. Every constant access requires runtime `asNumber()` casts.
- **Impact:** No typo protection. `CONSTANTS.DISCONT_RATE` would be `undefined` at runtime.
- **Recommendation:** Generate a strongly-typed interface from Python constants.

#### MAINT-09: Redis cache key naming inconsistency (camel vs snake)
- **Evidence:** `backend/app/core/cache.py:77` stores as `sessionSecretHash` (camelCase). `CachedSession` TypedDict uses `session_secret_hash`. Lines 100-107 translate.
- **Impact:** Error-prone translation layer. Silent `None` returns on key mismatch.
- **Recommendation:** Standardize on snake_case.

#### MAINT-10: No documentation of financial formulas in calculator
- **Evidence:** `tcoCalculator.ts` has no formula documentation for monthly payment (line 752), residual value (lines 772-786), or payload penalty (lines 667-682).
- **Impact:** Domain-specific financial logic is hard to verify or maintain without formula references.
- **Recommendation:** Add formula comments with mathematical notation and source references.

#### MAINT-11: Calculator uses hard-coded override limits, not OVERRIDE_LIMITS
- **Evidence:** `shared/calculator/tcoCalculator.ts:138`, `data/constants.py:85`. The calculator sanitizes overrides using inline numeric ranges instead of consuming the canonical `OVERRIDE_LIMITS` from generated constants.
- **Impact:** Limits can drift between the calculator and the frontend/backend validators that do use `OVERRIDE_LIMITS`. Adding or changing a limit requires updating multiple locations.
- **Recommendation:** Import and use `OVERRIDE_LIMITS` from `shared/data/constants.generated.ts` in the calculator's sanitization logic. This also supports the AI-01 refactor (data-driven sanitization).

#### MAINT-12: Duty-cycle validation diverges across layers
- **Evidence:** `frontend/src/state/tcoStore.ts:94` (store resets invalid values), `shared/calculator/tcoCalculator.ts:126` (normalizes to 100%), `backend/app/models/session.py:100` (rejects sums outside tolerance).
- **Impact:** Inconsistent behaviour between UI, calculator, and API. A duty-cycle input that the store silently "fixes" might be rejected by the backend or silently re-normalised by the calculator.
- **Recommendation:** Define a single shared validation policy (e.g., reject if sum deviates from 100% by more than a tolerance). Make corrections explicit and visible to users rather than silent.

### 4.5 Duplication & Dead Code

#### DEAD-01: Unused Python runtime dependencies
- **Evidence:** `requirements.txt` includes numpy, numpy-financial, pandas, plotly, rich, click. Grep of active codebase (excluding `archive/`) shows no imports.
- **Impact:** Docker image bloat. Vulnerability surface. ~115MB of unused libraries.
- **Recommendation:** Move to `requirements-scripts.txt`.

#### DEAD-02: Unused dev dependencies
- **Evidence:** `requirements-dev.txt` includes sphinx, sphinx-rtd-theme, jupyter, ipykernel, memory-profiler, line-profiler, py-spy, tox (no `tox.ini`), safety, interrogate. None used in CI or config.
- **Impact:** Excessive install time. `safety` has free API deprecation issues.
- **Recommendation:** Remove. Re-add if actively needed.

#### DEAD-03: `WizardVehicleStep` orphaned component
- **Evidence:** Not imported anywhere. See MAINT-05.

#### DEAD-04: `useVehicleCatalog` hook is vestigial
- **Evidence:** `frontend/src/hooks/useVehicleCatalog.ts:1-10`. Wraps static import in `useMemo` with `isLoading: false` hardcoded. Designed for async pattern that was replaced.
- **Impact:** Every consumer destructures `{ data: catalog, isLoading }` even though `isLoading` is always `false`.
- **Recommendation:** Replace with direct import.

#### DEAD-05: Audit reference codes throughout backend
- **Evidence:** `SEC-004`, `API-002`, `SEC-007` etc. in docstrings across `main.py`, `router.py`, `middleware.py`, `security.py`, `session.py`, `calculation.py`.
- **Impact:** Codes are meaningless without the audit plan. Read like checklist artifacts.
- **Recommendation:** Consolidate into `docs/security-requirements.md`. In code, reference the doc.

#### DEAD-06: Unused `fetchSession` API helper
- **Evidence:** `frontend/src/services/api.ts:49`. Defined but not referenced anywhere else in the codebase.
- **Impact:** Dead code. Maintenance noise.
- **Recommendation:** Remove, or add usage in a session resume flow if that feature is planned.

#### DEAD-07: Unused `ValueError` handler in router
- **Evidence:** `backend/app/api/router.py:112`. Catches `ValueError` from session creation, but the service never raises it.
- **Impact:** Dead exception branch. False sense of error handling coverage.
- **Recommendation:** Remove the `ValueError` catch or document the code path that could raise it.

### 4.6 Dependency Health

#### DEP-01: ESLint 8 and @typescript-eslint v6 are end-of-life
- **Evidence:** `package.json:42` has `eslint: ^8.57.0`, lines 37-38 have `@typescript-eslint v6`.
- **Impact:** No new rules or bug fixes. Legacy `.eslintrc.cjs` format deprecated.
- **Recommendation:** Plan migration to ESLint 9 flat config and @typescript-eslint v8.

#### DEP-02: Core Python dependencies moderately outdated
- **Evidence:** SQLAlchemy 2.0.25 (current 2.0.36+), FastAPI 0.128 (current 0.115+), pytest 7.4 (8.x available), black 23.7 (24.x available), mypy 1.5 (1.13+ available).
- **Impact:** Missing security patches and bug fixes.
- **Recommendation:** Schedule dependency update sweep. FastAPI needs careful migration.

#### DEP-03: `greenlet` explicitly pinned
- **Evidence:** `requirements.txt:25` pins `greenlet==3.3.0`.
- **Impact:** Can cause resolution conflicts when SQLAlchemy is updated.
- **Recommendation:** Remove explicit pin.

#### DEP-04: `prettier` installed but not enforced
- **Evidence:** `package.json:46` lists prettier. No CI check, no format script, no ESLint integration.
- **Impact:** Formatting not enforced. Inconsistent code style.
- **Recommendation:** Add `format:check` to CI or remove prettier.

#### DEP-05: CI uses `bun install` without `--frozen-lockfile`
- **Evidence:** `ci.yml:99,135,156` all run `bun install` without `--frozen-lockfile`.
- **Impact:** CI can resolve different dependency versions than lockfile specifies.
- **Recommendation:** Add `--frozen-lockfile` to all CI `bun install` commands.

#### DEP-06: `BUN_VERSION: 'latest'` in CI
- **Evidence:** `ci.yml:15` and `dependency-audit.yml:20`.
- **Impact:** Frontend builds not reproducible. Bun still makes breaking changes between minors.
- **Recommendation:** Pin to specific version.

#### DEP-07: No automated dependency update workflow
- **Evidence:** No Dependabot or Renovate configuration found. Dependencies are pinned (Python) or caret-ranged (frontend) without update automation.
- **Impact:** Security patches may be missed. Upgrades become batchy and risky over time.
- **Recommendation:** Add Dependabot or Renovate with monthly cadence for runtime deps, weekly for security-only patches.

### 4.7 Tests & Observability

#### TEST-01: Backend tests broken locally
- **Evidence:** `pytest-asyncio` incompatible with installed pytest version. `ImportError: cannot import name 'FixtureDef' from 'pytest'`.
- **Impact:** Cannot run backend tests locally. Blocks development.
- **Recommendation:** Reinstall venv deps. Ensure `requirements-dev.txt` versions are compatible.

#### TEST-02: Two frontend test failures — **RESOLVED**
- **Evidence:** `e2e/ui-redesign.spec.ts` loaded by Vitest (Playwright API conflict). `sessionLifecycle.test.ts:45` calls `vi.resetModules()` which doesn't exist.
- **Impact:** 141/143 tests pass but CI will report failure.
- **Recommendation:** Exclude `e2e/` from Vitest config. Fix the `resetModules` call.
- **Resolution (2026-02-06):** Fixed. `e2e/` excluded in `vitest.config.ts:24`, `vi.resetModules` call corrected. 142/142 tests now pass.

#### TEST-03: Vitest uses `node` environment, blocking component tests
- **Evidence:** `vitest.config.ts:21` sets `environment: 'node'`.
- **Impact:** Cannot test React components. Explains why zero component tests exist.
- **Recommendation:** Change to `'jsdom'` or `'happy-dom'`.

#### TEST-04: Verification tests cover only baseline scenario
- **Evidence:** All 33 test cases in `verification_data.json` use `"scenario_name": "baseline"`. No `technology_breakthrough` or `oil_crisis` cases.
- **Impact:** Python-TypeScript parity only guaranteed for baseline. Scenario trajectory code untested.
- **Recommendation:** Generate fixtures for each scenario.

#### TEST-05: Only one override test case in verification data
- **Evidence:** `verification_data.json` has a single `"BEV001-overrides"` entry. No diesel override test, no vehicle override test, no financed purchase override test.
- **Impact:** Override interaction logic barely covered.
- **Recommendation:** Add 3-4 additional override combinations.

#### TEST-06: No test for request size middleware
- **Evidence:** No test file targets `RequestSizeLimitMiddleware`. Critical DoS protection feature untested.
- **Recommendation:** Add tests for oversized requests (both Content-Length and chunked).

#### TEST-07: No test for rate limiting behavior
- **Evidence:** No test verifies rate limit enforcement.
- **Recommendation:** Add integration test that exceeds rate limit and verifies 429 response.

#### TEST-08: No test for session update authorization
- **Evidence:** PUT tests always include the correct secret. Missing: PUT without secret (401), PUT with wrong secret (403).
- **Recommendation:** Add both test cases.

#### TEST-09: Carbon cost test mutates shared state
- **Evidence:** `carbon-cost.test.ts:12-36` mutates `SCENARIO_DEFINITIONS.baseline` directly.
- **Impact:** State leak risk between tests.
- **Recommendation:** Deep-clone scenario before mutation.

#### TEST-10: No mypy in CI
- **Evidence:** No CI workflow runs mypy despite it being in `requirements-dev.txt`.
- **Impact:** Python type errors undetected in CI.
- **Recommendation:** Add `backend-typecheck` CI job.

#### TEST-11: No E2E tests in CI
- **Evidence:** Playwright installed and specs exist, but no CI workflow runs them.
- **Impact:** UI regressions reach main branch undetected.
- **Recommendation:** Add E2E job to CI.

#### OBS-01: No observability instrumentation
- **Evidence:** No OpenTelemetry, Prometheus, or Sentry integration found in backend or frontend code. No structured logging beyond Python's default logger.
- **Impact:** Harder to diagnose performance regressions or failures in production. No request-level tracing for debugging multi-service interactions.
- **Recommendation:** Start with structured logging and request metrics on key paths (session create/update, calculation). Add distributed tracing later as deployment matures.

### 4.8 Build/Deploy Ergonomics

#### OPS-01: No production deployment configuration
- **Evidence:** No production Dockerfile, no Kubernetes manifests, no Terraform, no Procfile. Only deployment hint is Replit URL in `.env.production.example`.
- **Impact:** No documented production deployment process.
- **Recommendation:** Create production Dockerfile and deployment guide.

#### OPS-02: No Python lockfile for transitive dependencies
- **Evidence:** `requirements.txt` pins direct deps but not transitive ones.
- **Impact:** Transitive deps can change between installs.
- **Recommendation:** Use `pip-tools` or `uv` to generate fully-resolved lockfile.

#### OPS-03: No bun cache in CI
- **Evidence:** CI caches pip but not bun/node_modules.
- **Impact:** Every frontend CI job installs from scratch (30-60s per job).
- **Recommendation:** Add `actions/cache` for `~/.bun/install/cache`.

#### OPS-04: Backend test job depends on lint job unnecessarily
- **Evidence:** `ci.yml:47` has `needs: backend-lint`. Tests and lint are independent.
- **Impact:** Lint runtime added to critical path.
- **Recommendation:** Remove dependency. `ci-success` gates on both already.

#### OPS-05: Docker compose `env_file` fails on fresh clone
- **Evidence:** `docker-compose.yml:25` references `backend/.env` which is in `.gitignore`.
- **Impact:** `docker compose up` fails after fresh clone.
- **Recommendation:** Make `env_file` optional or add setup step to README.

#### OPS-06: No health checks on Docker services
- **Evidence:** No `healthcheck` directives in `docker-compose.yml`. `depends_on` only checks container start.
- **Impact:** Backend can start before postgres/redis are ready.
- **Recommendation:** Add health checks for postgres and redis.

#### OPS-07: No automated staleness check for generated TypeScript files — **RESOLVED**
- **Evidence:** Generation script must be run manually. No CI enforcement.
- **Impact:** Python and TypeScript data layers can silently diverge.
- **Recommendation:** Add CI step that regenerates and checks for uncommitted diffs.
- **Resolution (2026-02-06):** Already implemented. `.github/workflows/data-sync-check.yml` runs the generation script and checks for uncommitted diffs.

#### OPS-08: Single Docker Compose file serves dev and production
- **Evidence:** `docker-compose.yml` uses `uvicorn --reload` and `bun run dev`. No separate production compose file exists.
- **Impact:** Risk of deploying with dev servers (hot reload, weaker security defaults, lower performance). The `UVICORN_RELOAD` guard helps but `bun run dev` has no equivalent gate.
- **Recommendation:** Split into `docker-compose.yml` (dev) and `docker-compose.prod.yml` with production-grade commands, or document the file as dev-only.

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

#### A11Y-01: Charts have no text alternative
- **Evidence:** All 5 chart components in `frontend/src/components/results/` render SVG without text alternatives.
- **Impact:** Primary output (cost comparisons) inaccessible to visually impaired users.
- **Recommendation:** Add `aria-label` descriptions and a toggleable data table fallback.

#### A11Y-02: `aria-current` misuse in wizard stepper
- **Evidence:** `WizardStepper.tsx:33` uses `aria-current={isActive}` which evaluates to `"true"` or `"false"`.
- **Impact:** Screen readers misinterpret current step.
- **Recommendation:** Use `aria-current={isActive ? 'step' : undefined}`.

#### A11Y-03: Error messages lack `role="alert"`
- **Evidence:** `Field.tsx:27` and `Select.tsx:34` render errors as plain `<span>`.
- **Impact:** Screen reader users not notified when validation errors appear.
- **Recommendation:** Add `role="alert"` to error spans.

#### A11Y-04: Color contrast failure for muted text
- **Evidence:** `tailwind.config.js:13`. `brand-muted` (#666666) on `brand-background` (#F4F4F3) gives ~3.9:1 contrast ratio, below WCAG AA 4.5:1 requirement.
- **Recommendation:** Darken to at least `#595959`.

#### A11Y-05: Vehicle chips use `div role="button"` instead of `<button>`
- **Evidence:** `WizardElectricStep.tsx:126-162`.
- **Impact:** Custom keyboard handling duplicates native button behavior.
- **Recommendation:** Replace with `<button>` element.

---

## 5. Prioritized Backlog

| ID | Title | Impact | Effort | Risk | Phase | Dependencies |
|----|-------|--------|--------|------|-------|-------------|
| TEST-01 | Fix backend test infrastructure (pytest-asyncio) | **High** | XS | Low | 1 | None |
| TEST-03 | Change Vitest env to jsdom | **High** | XS | Low | 1 | None |
| MAINT-01 | Pin ruff version consistently (local + CI) | **High** | XS | Low | 1 | None |
| DEP-05 | Add `--frozen-lockfile` to CI bun install | **High** | XS | Low | 1 | None |
| DEP-06 | Pin BUN_VERSION in CI | **High** | XS | Low | 1 | None |
| MAINT-03 | Add missing test deps to requirements-dev.txt | **High** | XS | Low | 1 | None |
| SEC-02 | Create .dockerignore files | **Med** | XS | Low | 1 | None |
| OPS-06 | Add Docker health checks | **Med** | S | Low | 1 | None |
| FE-01 | Add React Error Boundary | **Med** | S | Low | 1 | None |
| MAINT-07 | Enable react-hooks/recommended in ESLint | **Med** | XS | Low | 1 | None |
| SEC-05 | Narrow cache.py exception handling | **Med** | S | Low | 2 | None |
| CALC-05 | Align Python/TS rebate calculation logic | **Med** | S | Low | 2 | None |
| CALC-07 | Add BATTERY_REPLACEMENT_YEAR to Python constants | **Med** | XS | Low | 2 | Regen TS |
| CALC-08 | Remove per-vehicle maintenance_cost_per_km from catalog | **Med** | S | Low | 2 | Regen TS |
| TEST-04 | Add verification fixtures for all scenarios | **Med** | M | Low | 2 | Regen from Python |
| TEST-05 | Add override combination test cases | **Med** | M | Low | 2 | Regen from Python |
| TEST-06 | Add middleware tests | **Med** | S | Low | 2 | None |
| TEST-08 | Add session update auth tests | **Med** | S | Low | 2 | None |
| TEST-10 | Add mypy to CI | **Med** | S | Low | 2 | Fix mypy config |
| DEAD-01 | Remove unused Python runtime deps | **Med** | S | Low | 2 | Test Docker build |
| MAINT-02 | Consolidate on ruff (remove flake8/pylint) | **Med** | S | Low | 2 | None |
| AI-01 | Refactor repetitive sanitization to data-driven (preserve `clampOverrideAboveMin` special case for `annual_kms_variation`) | **Med** | M | Low | 2 | Test coverage first |
| PERF-01 | Add code splitting for ResultsPage | **Med** | M | Low | 2 | None |
| SEC-08 | Offload bcrypt to worker thread | **Med** | S | Low | 2 | None |
| MAINT-11 | Centralize calculator override limits from OVERRIDE_LIMITS | **Med** | M | Low | 2 | AI-01, Regen TS |
| MAINT-12 | Unify duty-cycle validation across layers | **Med** | M | Med | 2 | None |
| DEP-07 | Add Dependabot/Renovate for dependency updates | **Med** | S | Low | 2 | None |
| AI-07 | Surface frontend persist errors to users | **Med** | S | Low | 2 | FE-01 |
| FE-03 | PaybackChart: compute year-by-year cash flows | **Med** | M | Low | 2 | None |
| CALC-06 | Restructure CostBreakdown into named groups | **Med** | L | Med | 2 | See CALC-06 sub-plan |
| MAINT-08 | Generate strongly-typed constants interface | **Med** | M | Med | 3 | Update generator |
| MAINT-04 | Remove duplicates from constants.future.ts | **Low** | XS | Low | 2 | None |
| MAINT-05 | Delete dead WizardVehicleStep | **Low** | XS | Low | 2 | None |
| DEAD-02 | Remove unused dev dependencies | **Low** | S | Low | 2 | None |
| MAINT-06 | Extract buildComparisonPayload utility | **Low** | S | Low | 2 | None |
| BE-05 | Fix file handle leak in offline migration | **Low** | XS | Low | 2 | None |
| DEAD-06 | Remove unused fetchSession helper | **Low** | XS | Low | 2 | None |
| DEAD-07 | Remove unused ValueError handler | **Low** | XS | Low | 2 | None |
| FE-02 | Integrate VehicleParamsForm with RHF (architecture consistency, not correctness bug) | **Low** | M | Med | 3 | None |
| A11Y-01 | Add chart text alternatives | **Low** | M | Low | 3 | None |
| DEP-01 | Migrate ESLint 9 + @typescript-eslint v8 | **Low** | L | Med | 3 | None |
| SEC-01 | Add non-root Docker users | **Low** | S | Low | 3 | Dev-only (Replit manages prod containers) |
| OPS-01 | Document Replit deployment process | **Low** | S | Low | 3 | None |
| BE-04 | Fix scenario identifier drift (key vs label) | **Med** | M | Med | 3 | DB migration |
| OPS-08 | Split dev/prod Docker Compose configs | **Low** | S | Low | 3 | Dev-only convenience |
| OBS-01 | Add structured logging (Replit-compatible) | **Low** | M | Low | 3 | None |

*Size: XS=<1hr, S=1-4hr, M=4-16hr, L=16hr+*

---

## 6. Migration Plan

### Phase 1: Safety Rails (1-2 days)

**Goal:** Fix broken infrastructure and add guardrails. All changes are additive or fix-only. Zero functional changes.

1. Fix `requirements-dev.txt` (add httpx, factory-boy, anyio; pin compatible pytest-asyncio)
2. Pin ruff to same version in `requirements-dev.txt` and `ci.yml`
3. Pin `BUN_VERSION` in CI workflows
4. Add `--frozen-lockfile` to CI `bun install` commands
5. Change Vitest environment to `jsdom`
6. Add `react-hooks/recommended` to ESLint extends
7. Create `.dockerignore` files
8. Add Docker health checks for postgres/redis
9. Add Error Boundary to frontend

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

Remaining:
1. **Align CALC-05** (rebate logic): Fix whichever implementation is wrong
2. Add BATTERY_REPLACEMENT_YEAR to Python constants
3. **Fix CALC-08**: Remove `maintenance_cost_per_km` from vehicle catalog data (calculator already uses weight-class constants)
4. **Fix FE-03** (PaybackChart): Replace linear interpolation with year-by-year nominal cash flows
5. Add verification fixtures for all scenarios and override combinations

**CALC-06 sub-plan: Restructure CostBreakdown into named groups.**
This is a breaking change that touches multiple layers. Implementation sequence:
  - a. Define new `GroupedCostBreakdown` type in `shared/types/tco.types.ts` with `npv_costs`, `nominal_costs`, `upfront_costs` groups
  - b. Update calculator output in `tcoCalculator.ts` to produce the new structure
  - c. Update all 6 chart components in `frontend/src/components/results/` to consume the new structure
  - d. Update backend API response shapes and session storage serialization
  - e. Update or add migration for any stored session data that uses the old flat shape
  - f. Update verification data and parity tests
  - g. Remove old flat `CostBreakdown` type
  - **Risk mitigation:** Do this as a single PR to avoid intermediate broken states. Write the new type alongside the old one first, migrate consumers, then remove the old type.

**Test and CI improvements:**

1. Add middleware, rate limiting, and session auth tests
2. Add mypy to CI (fix config first)
3. Surface frontend persist/calculation errors to users (toast notifications)

**Cleanup and maintenance:**

1. Remove unused Python deps (runtime and dev)
2. Consolidate on ruff
3. Delete dead code (WizardVehicleStep, vestigial hook, constants.future.ts duplicates, fetchSession helper, unused ValueError handler)
4. Fix file handle leak in offline migration
5. Refactor repetitive sanitization to data-driven
6. Centralize calculator override limits from `OVERRIDE_LIMITS`
7. Unify duty-cycle validation across layers. **Implementation note:** Must be coordinated across all three layers (store, calculator, backend) simultaneously to avoid introducing new inconsistencies between layers during the transition.
8. Narrow cache module exception handling
9. Offload bcrypt to worker thread (`anyio.to_thread.run_sync`)
10. Add Dependabot/Renovate configuration

**Rollback:** Each item is a separate PR (except CALC-06 which is one atomic PR). Revert any single PR if issues arise.
**Verification:** Full CI pass. Calculator parity tests pass with updated verification data. Coverage increases.

### Phase 3: Structural Improvements (ongoing)

**Goal:** Larger improvements that require more coordination. Execute as capacity allows.

1. Generate strongly-typed constants interface from Python
2. Integrate VehicleParamsForm with React Hook Form
3. Add code splitting for ResultsPage/charts
4. Add component tests using React Testing Library
5. Migrate ESLint 9 + flat config
6. Add accessibility improvements (charts, stepper, error messages)
7. Document Replit deployment process
8. Add E2E tests to CI
9. Fix scenario identifier drift (store key alongside label, backfill existing rows)
10. Add structured logging (Replit-compatible)

**Approach:** Use Branch by Abstraction for the constants type change (add new typed interface alongside `ConstantCatalog`, migrate consumers, then remove the old type). Use feature flags or route-level code splitting for lazy loading.

**Note on deployment:** Production runs on Replit with a Replit-managed database. Docker hardening items (multi-stage builds, non-root users, dev/prod compose split) are lower priority since Replit manages the production container environment. Focus Docker improvements on local dev experience only.

---

## 7. Tooling & Guardrails Recommendations

### Automate in CI (new checks)

| Check | Tool | Config |
|-------|------|--------|
| Python type checking | mypy | Add `backend-typecheck` job |
| SAST security scan | bandit | `bandit -r backend/ -ll` in lint job |
| Generated file staleness | Custom script | Regenerate + `git diff --exit-code` |
| Frontend formatting | prettier | `prettier --check src/` |
| Frozen lockfile | bun | `bun install --frozen-lockfile` |
| Constants validation | Custom | Charging mix sums, rate ranges, trajectory lengths |

### Fix existing CI checks

| Issue | Fix |
|-------|-----|
| Ruff version drift | Pin same version in CI and `requirements-dev.txt` |
| BUN_VERSION: latest | Pin to specific version |
| Missing frozen lockfile | Add `--frozen-lockfile` to all `bun install` |
| Sequential backend jobs | Remove `needs: backend-lint` from `backend-test` |
| No bun cache | Add `actions/cache` for bun install cache |
| Vitest includes e2e | Exclude `e2e/` from Vitest glob |

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
| 5 | Cost breakdown structure (CALC-06) | **Restructure into named groups.** | Breaking change, but eliminates a real source of confusion. Detailed sub-plan in Phase 2. |
| 6 | PaybackChart (FE-03) | **Year-by-year cash flows.** | Users are making $200k+ purchasing decisions. Accuracy matters. |
| 7 | Deployment target | **Replit + Replit-managed database.** | Docker hardening items deprioritised accordingly. |

### Deferred Items (excluded from phased plan)

These items need further investigation before a decision can be made. They are excluded from the Phase 1-3 migration plan.

**Session secret flow (SEC-06/SEC-08):**
The session secret is returned in both JSON body and HttpOnly cookie. The JSON body is visible in dev tools and logs.
- *Questions to resolve:* Are there non-browser API consumers (scripts, Postman, tests) that rely on the JSON response? Is the cookie migration from localStorage complete? What breaks if the JSON body is removed? Is the dual-return a deliberate transitional design or an oversight?
- *If resolved:* Cookie-only is more secure. But removing JSON may break existing consumers.

**Request size middleware (BE-01):**
The middleware lets handlers run before rejecting oversized payloads (413). Chunked requests bypass the size check.
- *Questions to resolve:* What is the realistic threat model for a TCO calculator? Does Replit provide upstream request size limits that make this redundant? Do any endpoints write to the database before reading the full body (making partial writes a real risk)? Is the current behavior actually causing issues?
- *If resolved:* Fix is straightforward (abort before `call_next`) but may not be worth the effort given low risk at current scale.

### Assumptions (verified or updated)

- **Deployment target:** Replit with Replit-managed database. **Confirmed.** Docker hardening items are dev-environment-only improvements.
- **User base scale:** Recommendations assume moderate traffic (tens to low hundreds of concurrent users). Analytics N+1 queries and bcrypt overhead are acceptable at low scale but would need attention at higher traffic.
- **PostgreSQL version:** Docker compose uses `postgres:15-alpine`. Replit-managed DB version may differ.
- **Browser support:** No browserslist config found beyond the env var workaround. Assumed modern browsers (Chrome/Firefox/Safari/Edge latest 2 versions).
- **Session secret migration:** The code handles both cookie-based and header-based session secrets. Assumed this is transitional (see Deferred Items above).
- **Analytics performance targets:** No SLOs for analytics endpoints found. Current N-query approach (BE-03) is acceptable at current scale (~8 BEVs) but needs attention if the vehicle catalog grows.
- **Dependency update tooling:** No Dependabot or Renovate config was found. Assumed no hidden update automation exists elsewhere.

---

## 9. Appendix

### Baseline Health Snapshot (2026-02-06)

| Check | Status | Details |
|-------|--------|---------|
| Ruff (Python lint) | **PASS** | Clean |
| Black (formatting) | **PASS** | 43 files unchanged |
| isort (imports) | **PASS** | Clean |
| Backend tests (pytest) | **FAIL** | `ImportError: cannot import name 'FixtureDef' from 'pytest'` (pytest-asyncio incompatibility) |
| Data validation | **PASS** | 16 vehicles, 3 scenarios validated |
| TypeScript typecheck | **PASS** | Clean |
| ESLint (frontend) | **PASS** | Clean |
| Frontend tests (Vitest) | **PASS** | 142/142 pass (e2e excluded, resetModules fixed) |
| Bandit (security) | **BROKEN** | Missing `pbr` module dependency |
| pip-audit (vulns) | **PASS** | No known vulnerabilities |
| Vulture (dead code) | **PASS** | Nothing detected at 80% confidence |
| mypy (type check) | **FAIL** | Dual module name resolution conflict (config issue, not code error) |

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
| Docker | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |
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
