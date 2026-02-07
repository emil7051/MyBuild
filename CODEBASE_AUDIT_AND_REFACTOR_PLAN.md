# Executive Summary
This audit covers backend, frontend, shared calculator/data, scripts, and CI/deployment workflows.

Baseline health is strong: backend tests, frontend tests, lint/typecheck, and dependency audits passed (`tests`, `frontend`, `requirements*.lock.txt`). The main issues are in architectural consistency and guardrails rather than immediate runtime breakage.

Highest-priority risks:
1. Concurrency/state correctness in calculation orchestration (`frontend/src/hooks/useCalculations.ts:71-119`, `frontend/src/components/layout/AppShell.tsx:11`, `frontend/src/components/wizard/WizardCompareStep.tsx:13`).
2. Inconsistent comparison semantics across result charts (`frontend/src/components/results/SavingsWaterfallChart.tsx:68-84`, `frontend/src/components/results/PaybackChart.tsx:68-73`, `frontend/src/components/results/SensitivityTornadoChart.tsx:75-80`).
3. Security controls that can silently degrade (rate-limiting fail-open/per-process behavior) (`backend/app/core/security.py:95-109`, `backend/app/main.py:50-54`).
4. CI/test guardrails that are present but uneven (low backend coverage floor, narrow mypy scope, smoke-only E2E script) (`.github/workflows/ci.yml:67-73`, `.github/workflows/ci.yml:107-112`, `frontend/package.json:13`).

Recommendation: execute a phased remediation plan emphasizing safety rails first, then low-risk refactors, then structural changes. Several items can run in parallel (detailed in Migration Plan).

# Independent Verification Update (2026-02-07)
Independent source review was validated against the current repository state before implementation.

- Confirmed and integrated into this plan:
  - F1 scope expansion: dual `useCalculationRunner` instances make overlap a practical bug, not just a latent boolean-state race (`frontend/src/components/layout/AppShell.tsx:11`, `frontend/src/components/wizard/WizardCompareStep.tsx:13`, `frontend/src/hooks/useCalculations.ts:46-49`).
  - Missing chart-level error isolation (`frontend/src/components/results/ResultsPanel.tsx:91-174`, `frontend/src/main.tsx:15-20`).
  - Unused autosave state causes unnecessary rerenders (`frontend/src/hooks/useWizardAutosave.ts:14`, `frontend/src/pages/WizardPage.tsx:58`).
  - Comparison semantic split extends beyond deep-analysis charts: `ComparisonHighlights` ranks all vehicles by `total_cost` regardless of drivetrain (`frontend/src/components/results/ComparisonHighlights.tsx:23-25`).
  - Migration URL conversion is brittle to driver variants (`backend/app/db/session.py:61-68`).
  - API client surface omits `getSession` despite backend endpoint availability (`frontend/src/services/api.ts:27-43`, `backend/app/api/router.py:143-167`).
  - H3 drift risk is amplified by unchecked cast (`frontend/src/forms/wizardForm.ts:13`).
  - Additional CI workflow exists and should be documented (`.github/workflows/claude-review.yml:1-37`).
- Scope adjustments:
  - `S2` reclassified from security defect to architecture/configuration guardrail. Cookie-based auth intentionally requires credentialed requests; focus is documentation and config assertions (`frontend/src/services/api.ts:12`, `backend/app/main.py:58-64`, `backend/app/core/config.py:174-181`, `API.md:14-20`).
  - `M4` narrowed: only `per-file-ignores` is deprecated in current Ruff warning output.
  - `H1` clarified: lockfiles are not corrupted; local environment has stale `bandit` (`1.7.0`) while lockfile pins `1.9.3`.
- External claims rejected after direct verification:
  - `F5` should **not** be dropped on this stack. In current dependencies (`starlette==0.50.0`), `HTTP_422_UNPROCESSABLE_ENTITY` emits a deprecation warning and `HTTP_422_UNPROCESSABLE_CONTENT` exists.
  - `bandit==1.9.3` **does** exist on PyPI; issue is local install drift, not invalid pin.

# Completion Verification + Migration Debt Cleanup (2026-02-07)
Parallel sub-agent verification across backend, frontend, shared/scripts, and CI/docs confirmed that all findings marked `DONE` are implemented in current code.

- Additional migration-tech-debt cleanup completed during verification:
  - Removed legacy client cache payload compatibility branch (`sessionSecretHash` fallback) in `backend/app/core/cache.py`.
  - Removed unused legacy store setter `setIsCalculating` in `frontend/src/state/tcoStore.ts`.
  - Finalized `P3` persistence cleanup by no longer persisting `results` and clearing legacy hydrated result payloads in `frontend/src/state/tcoStore.ts`.
- Verification checks executed after cleanup:
  - `python -m pytest tests --cov` ✅
  - `cd frontend && bun run test` ✅
  - `cd frontend && bun run lint` ✅
  - `cd frontend && bun run typecheck` ✅
- Scope note:
  - `archive/` remains intentionally legacy-only and isolated from active runtime paths.

# Repo Overview
- Architecture map
  - Backend API: FastAPI app, middleware, routing, DB initialization (`backend/app/main.py:36-98`, `backend/app/api/router.py:33-186`, `backend/app/db/session.py:39-79`).
  - Persistence: SQLAlchemy models + Alembic migrations (`backend/app/db/models.py:29-171`, `backend/alembic/versions/*.py`).
  - Frontend: React app shell + wizard + results routes (`frontend/src/main.tsx:12-23`, `frontend/src/App.tsx:14-29`, `frontend/src/pages/WizardPage.tsx:51-206`, `frontend/src/pages/ResultsPage.tsx:8-45`).
  - Shared computation: TypeScript TCO engine and generated catalogs (`shared/calculator/tcoCalculator.ts:935-986`, `shared/data/vehicleCatalog.ts:9`, `shared/data/scenarios.ts:5`, `shared/data/constants.generated.ts:3`).
  - Data source of truth: Python data modules and generator (`data/*.py`, `scripts/generate_vehicle_catalog_ts.py:14-27`, `scripts/generate_vehicle_catalog_ts.py:202-223`).
- Key entry points
  - API/runtime: `backend/app/main.py:98`
  - API router: `backend/app/api/router.py:33`
  - Frontend runtime: `frontend/src/main.tsx:12`
  - Shared calculator API: `shared/calculator/index.ts:1-7`
  - Data generation CLI: `scripts/generate_vehicle_catalog_ts.py:225-226`
- Dependency map
  - Python runtime/security/observability dependencies are pinned in `requirements.txt` and lockfiles (`requirements.txt`, `requirements.lock.txt`).
  - Frontend dependencies/scripts are in `frontend/package.json:6-57`.
  - CI quality gates and dependency auditing are in `.github/workflows/ci.yml:17-287`, `.github/workflows/dependency-audit.yml:22-170`, `.github/workflows/data-sync-check.yml:19-56`.
  - Automated PR AI review is also configured via `.github/workflows/claude-review.yml:1-37`.

# Top Risks and Hotspots
(Top 10, ranked by likelihood x impact)

| Rank | Risk | Likelihood | Impact | Score | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Dual `useCalculationRunner` instances plus global `isCalculating` allow real overlapping mutations and stale loading state | High | High | 9 | `frontend/src/components/layout/AppShell.tsx:11`, `frontend/src/components/wizard/WizardCompareStep.tsx:13`, `frontend/src/hooks/useCalculations.ts:46-49`, `frontend/src/hooks/useCalculations.ts:79-119` |
| 2 | Chart comparison policy inconsistency (best BEV vs first BEV vs overall ranking) can produce conflicting business narratives | High | High | 9 | `frontend/src/components/results/SavingsWaterfallChart.tsx:70-84`, `frontend/src/components/results/PaybackChart.tsx:68-73`, `frontend/src/components/results/SensitivityTornadoChart.tsx:75-80`, `frontend/src/components/results/ComparisonHighlights.tsx:23-25` |
| 3 | Rate limiting can be silently disabled/degraded depending on dependency/storage availability | Medium | High | 8 | `backend/app/core/security.py:95-109`, `backend/app/main.py:50-54` |
| 4 | Corrupted Redis cache payload can bubble a JSON decode exception through session reads | Medium | High | 8 | `backend/app/core/cache.py:107-119`, `backend/app/services/sessions.py:169-173`, `tests/test_cache.py:132-145` |
| 5 | Session pending-update policy is implicit and can discard older wizard-only updates by design | Medium | High | 8 | `frontend/src/services/sessionLifecycle.ts:98-106`, `frontend/src/test/sessionLifecycle.test.ts:72-115` |
| 6 | Single chart render error can crash the entire app due coarse ErrorBoundary scope | Medium | Medium | 6 | `frontend/src/components/results/ResultsPanel.tsx:91-174`, `frontend/src/main.tsx:15-20` |
| 7 | Request-size middleware buffers full bodies in memory before dispatch | Medium | Medium | 6 | `backend/app/core/middleware.py:52-87` |
| 8 | CI E2E job runs only smoke spec, leaving broader UI spec out of default path | Medium | Medium | 6 | `frontend/package.json:13`, `.github/workflows/ci.yml:218-220`, `frontend/e2e/ui-redesign.spec.ts:1-123` |
| 9 | Data contract drift risk: generated scenario map vs manual `ScenarioKey` plus unchecked cast in form layer | Medium | Medium | 6 | `scripts/generate_vehicle_catalog_ts.py:120-126`, `shared/types/tco.types.ts:10`, `frontend/src/forms/wizardForm.ts:13`, `.github/workflows/data-sync-check.yml:41-55` |
| 10 | Tooling hygiene warnings indicate preventable maintenance drag | High | Low | 5 | `pyproject.toml:28-35`, `backend/alembic.ini:1-22`, `backend/app/api/router.py:65-67` |

# Findings (by Category)

## Correctness and Reliability

### Finding F1 - DONE
- Issue: Calculation orchestration is split across two hook instances while loading state is modeled as a single global boolean.
- Evidence:
  - Hook-scoped dedup refs: `frontend/src/hooks/useCalculations.ts:46-49`
  - `frontend/src/hooks/useCalculations.ts:79-95`
  - `frontend/src/hooks/useCalculations.ts:106-119`
  - Separate runner instance in header: `frontend/src/components/layout/AppShell.tsx:11`
  - Separate runner instance in wizard: `frontend/src/components/wizard/WizardCompareStep.tsx:13`
- Impact: Requests can overlap across instances and the UI may re-enable actions while work is still in progress.
- Root cause hypothesis: Shared global flag + per-instance dedup refs that do not coordinate across components.
- Recommendation: Centralize orchestration (store-level singleton/service) and derive loading from authoritative in-flight counts (`useIsMutating` or store counter).
- Tradeoffs: Slightly more state complexity; significantly better correctness under overlap.
- Migration/compatibility considerations: Keep backwards-compatible selector API (`isCalculating`) while unifying runner ownership.
- Test/verification plan: Add overlapping mutation tests for cross-instance compare + compare and compare + single scenarios.

### Finding F2 - DONE
- Issue: Results components use multiple comparison-selection policies without a shared contract.
- Evidence:
  - Best-BEV logic: `frontend/src/components/results/SavingsWaterfallChart.tsx:70-84`
  - First-BEV logic: `frontend/src/components/results/PaybackChart.tsx:68-73`
  - First-BEV logic: `frontend/src/components/results/SensitivityTornadoChart.tsx:75-80`
  - Overall lowest-cost ranking across all drivetrains: `frontend/src/components/results/ComparisonHighlights.tsx:23-25`
- Impact: Users can receive contradictory conclusions from different components on the same run.
- Root cause hypothesis: Chart-local selection logic with no shared policy function.
- Recommendation: Implement a shared selector contract (`selectComparisonPair`) for diesel-vs-BEV charts and explicitly document `ComparisonHighlights` as either aligned or intentionally different.
- Tradeoffs: Requires product decision (best BEV vs user-selected BEV).
- Migration/compatibility considerations: Existing snapshot tests for charts will need updates.
- Test/verification plan: Add one unit test that asserts consistent vehicle pair across `Payback`, `Waterfall`, and `Tornado`, plus one assertion covering `ComparisonHighlights` policy intent.

### Finding F3 - DONE
- Issue: Pending session update reconciliation intentionally prefers results update in one branch and can skip wizard-only update.
- Evidence:
  - Policy logic: `frontend/src/services/sessionLifecycle.ts:98-106`
  - Behavior coverage: `frontend/src/test/sessionLifecycle.test.ts:72-115`
- Impact: Not always wrong, but behavior is implicit and brittle if payload semantics change.
- Root cause hypothesis: Timestamp-based “last-writer” policy with type-based buckets (`hasResults`).
- Recommendation: Make policy explicit via one of two options: (A) deep-merge payloads per field, (B) retain current behavior but codify in docs/tests as intentional contract.
- Tradeoffs:
  - A: safer semantics, more implementation complexity.
  - B: simpler runtime, but higher future regression risk.
- Migration/compatibility considerations: Requires backend partial-update semantics validation.
- Test/verification plan: Add explicit tests for both payload ordering and merge behavior decision.

### Finding F4 - DONE
- Issue: Corrupted cache JSON propagates decode errors in session retrieval path.
- Evidence:
  - Decode without guard: `backend/app/core/cache.py:107-119`
  - Call site uses cached path directly: `backend/app/services/sessions.py:169-173`
  - Test confirms propagation: `tests/test_cache.py:132-145`
- Impact: Single bad cache entry can surface as API failure instead of graceful DB fallback.
- Root cause hypothesis: JSON decode path not treated as recoverable cache failure.
- Recommendation: Catch `json.JSONDecodeError`, evict bad key, and continue to DB fallback.
- Tradeoffs: Masks corruption incidents unless coupled with warning metrics.
- Migration/compatibility considerations: Backward compatible; no contract changes.
- Test/verification plan: Add API-level test proving graceful fallback from corrupted cache.

### Finding F5 - DONE
- Issue: Deprecated HTTP status constant is used for UUID validation errors.
- Evidence:
  - `backend/app/api/router.py:65-67`
  - Runtime warning during tests: `python -m pytest tests --cov` output (DeprecationWarning).
- Impact: Future framework upgrades may break or alter behavior.
- Root cause hypothesis: Framework API drift.
- Recommendation: Move to `HTTP_422_UNPROCESSABLE_CONTENT` (or equivalent current constant in FastAPI/Starlette stack).
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Ensure clients still treat response as 422 class.
- Test/verification plan: Existing security tests for invalid UUID should remain green.

### Finding F6 - DONE
- Issue: Results charts rely on Suspense fallbacks but lack chart-level ErrorBoundary isolation.
- Evidence:
  - Chart loading boundaries only: `frontend/src/components/results/ResultsPanel.tsx:91-174`
  - App-wide boundary catches all render errors: `frontend/src/main.tsx:15-20`
- Impact: A single chart render exception can blank the full app shell instead of degrading one panel.
- Root cause hypothesis: Error containment is only implemented at application root.
- Recommendation: Wrap each chart (or each chart group) in a local ErrorBoundary with a chart-specific fallback.
- Tradeoffs: Slight wrapper complexity and one extra component.
- Migration/compatibility considerations: Keep current top-level boundary as global last resort.
- Test/verification plan: Add one test that injects a throwing chart and verifies other panels remain visible.

## Security and Privacy

### Finding S1 - DONE
- Issue: Rate-limiter protection can fail open (missing `slowapi`) or degrade to per-process limits (no storage backend).
- Evidence:
  - No-op limiter fallback: `backend/app/core/security.py:75-84`, `backend/app/core/security.py:105-109`
  - Per-process warning path: `backend/app/core/security.py:99-103`
  - App only wires exception handler when dependency present: `backend/app/main.py:50-54`
- Impact: Abuse resistance and quota semantics are environment-dependent and can silently degrade.
- Root cause hypothesis: Optional dependency pattern without environment policy enforcement.
- Recommendation: Fail startup in non-development when `slowapi` or shared storage is unavailable.
- Tradeoffs: Stricter deploy requirements; materially better security predictability.
- Migration/compatibility considerations: Provide escape hatch env var for emergency read-only modes.
- Test/verification plan: Add startup validation tests for production env permutations.

### Finding S2 - DONE
- Issue: Frontend Axios client globally enables credentials for all API requests as part of cookie-session architecture.
- Evidence:
  - `frontend/src/services/api.ts:9-13`
- Impact: Primary risk is misconfiguration/documentation drift, not an immediate exploit in current setup.
- Root cause hypothesis: Required runtime invariant (trusted API origin + explicit CORS allowlist) is implicit rather than enforced/documented end-to-end.
- Recommendation: Keep `withCredentials: true`, document architecture invariants, and add config assertions (trusted API URL rules in frontend and explicit origin policy in deployment docs).
- Tradeoffs: Slightly more configuration governance; avoids breaking intended cookie auth flows.
- Migration/compatibility considerations: Add explicit env docs and startup/config checks without changing default runtime behavior.
- Test/verification plan: Add config test matrix (same-origin, trusted cross-origin, untrusted cross-origin).

### Finding S3 - DONE
- Issue: Production-sensitive defaults exist for `database_url` and `redis_url` and can be used if env is incomplete.
- Evidence:
  - `backend/app/core/config.py:22-29`
- Impact: Misconfigured production environment can accidentally use local/dev defaults.
- Root cause hypothesis: Convenience defaults not gated by environment type.
- Recommendation: Enforce “must provide explicit URLs” when `environment != development`.
- Tradeoffs: Slightly stricter deployment configuration process.
- Migration/compatibility considerations: Roll out with warning-only mode first, then hard-fail.
- Test/verification plan: Add config tests for production env requiring explicit URLs.

## Performance

### Finding P1 - DONE
- Issue: Payback chart recomputes nominal timelines on broad `wizardData` dependency changes.
- Evidence:
  - Heavy calculation in memo: `frontend/src/components/results/PaybackChart.tsx:75-138`
  - Full dependency object: `frontend/src/components/results/PaybackChart.tsx:138`
- Impact: Potential UI jank during frequent form changes.
- Root cause hypothesis: Memo key is wider than actual inputs.
- Recommendation: Hash only relevant payback inputs or memoize timelines by normalized payload key.
- Tradeoffs: Adds key-management complexity.
- Migration/compatibility considerations: Ensure key includes all financially relevant fields.
- Test/verification plan: Add profiling benchmark and regression threshold in CI.

### Finding P2 - DONE
- Issue: Request-size middleware buffers entire body before handing off to app.
- Evidence:
  - `backend/app/core/middleware.py:52-87`
- Impact: Higher memory pressure and potential amplification under concurrent large requests.
- Root cause hypothesis: Chosen implementation prioritizes pre-route rejection semantics.
- Recommendation: Keep pre-check, but stream through with bounded chunk accounting and avoid full body join when possible.
- Tradeoffs: More complex ASGI receive wrapper logic.
- Migration/compatibility considerations: Preserve semantics for handlers expecting full body.
- Test/verification plan: Add stress tests for many near-limit concurrent requests.

### Finding P3 - DONE
- Issue: Local storage persistence includes full `results` and `vehicleDetails` payloads.
- Evidence:
  - `frontend/src/state/tcoStore.ts:141-147`
- Impact: Larger hydration payload and potential storage overhead.
- Root cause hypothesis: Convenience persistence scope.
- Recommendation: Persist minimal state (`wizardData`, `sessionId`, catalog version), derive `vehicleDetails` from shared catalog at runtime.
- Tradeoffs: Slightly more recomputation on hydration; lower storage overhead.
- Migration/compatibility considerations: Add store schema migration for older persisted data.
- Test/verification plan: Add hydration-size budget and migration tests.
- Implementation status:
  - `vehicleDetails` is reconstructed from the shared catalog on hydration.
  - Persisted state now excludes `results`; legacy hydrated `results` payloads are explicitly dropped during rehydration.

### Finding P4 - DONE
- Issue: `useWizardAutosave` tracks `saveStatus` state that is never consumed by callers.
- Evidence:
  - State is updated in hook: `frontend/src/hooks/useWizardAutosave.ts:14`, `frontend/src/hooks/useWizardAutosave.ts:40-48`, `frontend/src/hooks/useWizardAutosave.ts:69-82`
  - Hook return value is ignored at callsite: `frontend/src/pages/WizardPage.tsx:58`
- Impact: Autosave transitions trigger avoidable rerenders in the wizard subtree.
- Root cause hypothesis: UI status indicator was started but not integrated.
- Recommendation: Either surface `saveStatus` in UI (e.g., "Saving/Saved/Error") or remove state tracking until it is needed.
- Tradeoffs: Keeping it improves UX but adds UI work; removing it reduces rerender churn now.
- Migration/compatibility considerations: Backward compatible either way.
- Test/verification plan: Add render-count/perf assertion for autosave transitions.

## Maintainability

### Finding M1 - DONE
- Issue: Observability responsibilities were consolidated in one file with import-time initialization side effects.
- Evidence:
  - Modularized observability package:
    - `backend/app/core/observability/logging.py`
    - `backend/app/core/observability/tracing.py`
    - `backend/app/core/observability/metrics.py`
    - `backend/app/core/observability/alerts.py`
    - `backend/app/core/observability/middleware.py`
    - `backend/app/core/observability/runtime.py`
  - Startup wiring now injects dependencies explicitly: `backend/app/main.py`
  - Unit + integration coverage:
    - `tests/test_observability_modules.py`
    - `tests/test_middleware.py`
- Impact: Lower coupling and safer, more targeted testability for observability behavior.
- Root cause hypothesis: Centralized incremental additions over time.
- Recommendation: Keep module boundaries and dependency injection pattern for future observability changes.
- Tradeoffs: More files and explicit wiring in app startup.
- Migration/compatibility considerations: Public imports remain available from `backend.app.core.observability`.
- Test/verification plan:
  - `python -m pytest tests/test_middleware.py tests/test_observability_modules.py`
  - `python -m pytest tests --cov`
- Implementation status:
  - Removed monolithic `backend/app/core/observability.py`.
  - Added runtime factory (`create_observability_runtime`) and injected middleware dependencies at app creation time.

### Finding M2 - DONE
- Issue: Generator establishes `REPO_ROOT` but output paths remain working-directory relative.
- Evidence:
  - Root calculation: `scripts/generate_vehicle_catalog_ts.py:14-16`
  - Relative output paths: `scripts/generate_vehicle_catalog_ts.py:23-26`
- Impact: Running generator from non-repo root can write artifacts to wrong location or fail unexpectedly.
- Root cause hypothesis: Mixed assumptions about invocation directory.
- Recommendation: Anchor outputs to `REPO_ROOT / "shared/data/..."`.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Backward compatible.
- Test/verification plan: Add generator test that executes from a different CWD.
- Implementation status:
  - Output paths are anchored to `REPO_ROOT` in `scripts/generate_vehicle_catalog_ts.py`.
  - Regression coverage added in `tests/test_generate_vehicle_catalog_script.py`.

### Finding M3 - DONE
- Issue: Multiple route handlers duplicate session-secret extraction/refresh behavior.
- Evidence:
  - `backend/app/api/router.py:132-138`
  - `backend/app/api/router.py:160-164`
- Impact: Drift risk when cookie policy changes.
- Root cause hypothesis: Copy/paste route-level logic.
- Recommendation: Extract dependency/helper that handles secret lifecycle once.
- Tradeoffs: Small abstraction overhead.
- Migration/compatibility considerations: Keep response/cookie contract unchanged.
- Test/verification plan: Re-run existing auth tests plus add one shared helper test.

### Finding M4 - DONE
- Issue: Ruff config drift warning is limited to deprecated top-level `per-file-ignores`.
- Evidence:
  - `pyproject.toml:28-35`
  - `python -m ruff check ...` warning explicitly flags only `per-file-ignores -> lint.per-file-ignores`.
- Impact: Future lint upgrades may break unexpectedly.
- Root cause hypothesis: Ruff config schema changed.
- Recommendation: Move only `per-file-ignores` into `[tool.ruff.lint]` and leave valid top-level keys (`line-length`, `target-version`, `extend-exclude`) unchanged.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Validate same effective ignore behavior post-migration.
- Test/verification plan: Run `ruff check` before/after and compare diagnostics.

### Finding M5 - DONE
- Issue: Frontend API client now exposes `getSession`, matching backend support for `GET /sessions/{session_id}`.
- Evidence:
  - Backend endpoint exists: `backend/app/api/router.py:143-167`
  - Frontend now exports `getSession`: `frontend/src/services/api.ts:45-54`
  - API client coverage added: `frontend/src/test/apiClient.test.ts:1-57`
- Impact: Session-resume flows now have an explicit typed client helper instead of requiring ad hoc fetch logic.
- Root cause hypothesis: Initial frontend workflow relied on optimistic create/update path only.
- Recommendation: Use shared `getSession` helper for future resume/refetch flows to keep client behavior centralized.
- Tradeoffs: Minimal additional API-client surface.
- Migration/compatibility considerations: Backward compatible.
- Test/verification plan: `frontend/src/test/apiClient.test.ts` validates typed payload mapping for `getSession`.

## Duplication and Dead Code

### Finding D1 - DONE
- Issue: Empty-state chart UI is duplicated across several result components.
- Evidence:
  - `frontend/src/components/results/CostBreakdownChart.tsx:196-205`
  - `frontend/src/components/results/CostPerKmChart.tsx:84-93`
  - `frontend/src/components/results/SavingsWaterfallChart.tsx:182-190`
  - `frontend/src/components/results/SensitivityTornadoChart.tsx:161-169`
  - `frontend/src/components/results/PaybackChart.tsx:140-146`
- Impact: Inconsistent messaging/styling risk and repetitive maintenance.
- Root cause hypothesis: Component-local duplication.
- Recommendation: Create shared `EmptyChartState` component.
- Tradeoffs: Slight indirection.
- Migration/compatibility considerations: Keep component-specific message support.
- Test/verification plan: Snapshot tests for shared empty state across variants.

### Finding D2 - DONE
- Issue: `runSingle` and mutation status fields were unused by UI codepaths.
- Evidence:
  - Dead surface removed from hook export shape: `frontend/src/hooks/useCalculations.ts:116-137`
  - Orchestration coverage updated to validate overlap semantics using comparison-only paths: `frontend/src/test/useCalculations.orchestration.test.ts:230-278`
- Impact: Reduced API surface and maintenance burden in calculation orchestration.
- Root cause hypothesis: Incomplete/abandoned feature path.
- Recommendation: Reintroduce a single-calculation path only when a concrete UI flow and owner exist.
- Tradeoffs: Future single-run feature work will re-add API intentionally rather than carrying dormant code.
- Migration/compatibility considerations: Backward compatible for current app behavior because no production callsites consumed removed exports.
- Test/verification plan: `frontend/src/test/useCalculations.orchestration.test.ts` validates dedupe and in-flight counter behavior post-removal.

### Finding D3 - DONE
- Issue: Legacy scenario globals/functions in `data/scenarios.py` were unused by the active codebase and only referenced from archived modules.
- Evidence:
  - Removed legacy mutable API from active module (`active_scenario`, `set_active_scenario`, `get_active_scenario`, `create_custom_scenario`) in `data/scenarios.py`.
  - Updated archived callsites to use explicit baseline selection via `SCENARIOS["baseline"]`:
    - `archive/calculations_legacy/inputs.py`
    - `archive/legacy/analysis/generate_tco_analysis.py`
- Impact: Reduced dead code and made active scenario data module stateless/explicit.
- Root cause hypothesis: Legacy CLI/stateful scenario workflow remained in active data source module after architectural migration.
- Recommendation: Keep archive-only behavior isolated under `archive/` and avoid reintroducing mutable globals in active data modules.
- Tradeoffs: Any ad hoc script relying on removed helpers must switch to explicit scenario lookup.
- Migration/compatibility considerations: Archive references were updated in-tree to avoid breakage.
- Test/verification plan:
  - `python scripts/validation.py` ✅
  - `python -m pytest tests/test_scenario_contract.py` ✅
  - `cd frontend && bun run test` (parity suite included) ✅

## Dependency Health

### Finding H1 - DONE
- Issue: Runtime and dev lockfiles are healthy, but local static security scanning (`bandit`) can fail when the environment drifts from lockfile versions.
- Evidence:
  - `python -m pip_audit -r requirements.lock.txt --strict`: no known vulnerabilities.
  - `python -m pip_audit -r requirements-dev.lock.txt --strict`: no known vulnerabilities.
  - Lockfiles pin `bandit==1.9.3`: `requirements-dev.txt:33`, `requirements-dev.lock.txt:23`
  - Local env currently has stale `bandit==1.7.0`: `python -m pip show bandit`
  - `python -m bandit -r backend data scripts -q` failed with `ModuleNotFoundError: No module named 'pbr'`.
- Impact: Security linting can be skipped or produce noisy false setup failures.
- Root cause hypothesis: Local virtualenv drift rather than lockfile corruption.
- Recommendation: Re-sync dev env from lockfile (`pip install -r requirements-dev.lock.txt`) and run `bandit` in CI for deterministic enforcement.
- Tradeoffs: Slightly more maintenance for dev-tool dependencies.
- Migration/compatibility considerations: Prefer CI-owned bandit execution for determinism.
- Test/verification plan: Add a CI bandit job and make it non-blocking first.

### Finding H2 - DONE
- Issue: Backend mypy job only checks a subset of backend modules.
- Evidence:
  - `.github/workflows/ci.yml:107-112`
- Impact: Typed regressions in services/db/models may not be caught by CI.
- Root cause hypothesis: Gradual typing rollout paused at core/api surface.
- Recommendation: Expand mypy scope incrementally (`backend/app/services`, `backend/app/db`, then full backend app).
- Tradeoffs: Initial type-fix workload.
- Migration/compatibility considerations: Use phased strictness and excludes to avoid blocking all PRs immediately.
- Test/verification plan: Track mypy error count down to zero as rollout metric.

### Finding H3 - DONE
- Issue: Data-sync workflow validates drift only in `shared/data`, while type-level scenario contract safety is partially bypassed in frontend form code.
- Evidence:
  - Drift check scope: `.github/workflows/data-sync-check.yml:43-55`
  - Scenario key union is manual: `shared/types/tco.types.ts:10`
  - Generator emits scenarios dynamically: `scripts/generate_vehicle_catalog_ts.py:120-126`
  - Frontend casts runtime keys directly to union type: `frontend/src/forms/wizardForm.ts:13`
- Impact: Contract mismatches can surface later in unrelated CI stages or local runtime.
- Root cause hypothesis: Workflow optimized for generated file drift but not contract semantics, plus unchecked key casting.
- Recommendation: Add contract check (e.g., script asserting `SCENARIOS.keys()` == `ScenarioKey` union) and replace unchecked cast with validated assertion helper.
- Tradeoffs: Extra maintenance for check script.
- Migration/compatibility considerations: Keep failing output actionable (exact missing/extra keys).
- Test/verification plan: Add fixture test covering scenario key parity and form-schema key validation.

## Tests and Observability

### Finding T1 - DONE
- Issue: Custom pytest marker `enable_redis_cache` is used but not registered, causing warnings.
- Evidence:
  - Marker usage: `tests/test_cache.py:11`
  - Marker checks in fixture: `tests/conftest.py:45`
  - Runtime warning observed in `pytest` output.
- Impact: Warning noise can hide real warnings.
- Root cause hypothesis: Missing pytest marker config.
- Recommendation: Register marker in `pyproject.toml` `[tool.pytest.ini_options] markers`.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Backward compatible.
- Test/verification plan: Re-run `pytest` and verify warning removed.

### Finding T2 - DONE
- Issue: Backend coverage threshold is low relative to current achieved coverage, and critical module coverage is uneven.
- Evidence:
  - CI threshold: `.github/workflows/ci.yml:67-73` (`--cov-fail-under=60`)
  - Current run: total 88%; `backend/app/db/session.py` at 44% (from `pytest --cov` output).
- Impact: Regressions can slip even while CI remains green.
- Root cause hypothesis: Threshold set for early bootstrap phase and never raised.
- Recommendation: Raise threshold gradually (e.g., 70 -> 80 -> 85) and add targeted tests for low-coverage hotspots.
- Tradeoffs: Temporary PR friction while closing gaps.
- Migration/compatibility considerations: Roll out in small increments over multiple PRs.
- Test/verification plan: Track per-module coverage trend in CI.

### Finding T3 - DONE
- Issue: Frontend runtime failures are largely reported through `console.*` and toasts; no centralized client telemetry.
- Evidence:
  - `frontend/src/hooks/useCalculations.ts:61-65`, `frontend/src/hooks/useCalculations.ts:87-91`
  - `frontend/src/hooks/useWizardAutosave.ts:47-52`, `frontend/src/hooks/useWizardAutosave.ts:80-85`
  - `frontend/src/components/shared/ErrorBoundary.tsx:25`
- Impact: Production incident triage depends on user reports rather than measurable signals.
- Root cause hypothesis: Observability investment focused on backend only.
- Recommendation: Add lightweight client error reporting with redaction policy and environment gating.
- Tradeoffs: Additional dependency and privacy review required.
- Migration/compatibility considerations: Ensure no PII leakage in payloads.
- Test/verification plan: Synthetic error in staging should appear in telemetry sink.

### Finding T4 - DONE
- Issue: E2E script in default CI path runs only smoke spec; broader UI spec and screenshots are excluded.
- Evidence:
  - Script: `frontend/package.json:13`
  - CI invocation: `.github/workflows/ci.yml:218-220`
  - Additional spec exists: `frontend/e2e/ui-redesign.spec.ts:1-123`
- Impact: UI regressions may not be caught before merge.
- Root cause hypothesis: Runtime optimization favored smoke tests.
- Recommendation: Introduce `test:e2e:full` for nightly/release gates while retaining smoke on PR path.
- Tradeoffs: Longer CI for full suite.
- Migration/compatibility considerations: Snapshot stability across environments must be handled.
- Test/verification plan: Add scheduled full E2E workflow with artifact upload and flake tracking.

## Build/Deploy Ergonomics

### Finding B1 - DONE
- Issue: Playwright uses dev server for E2E, which can diverge from production build behavior.
- Evidence:
  - `frontend/playwright.config.ts:24-28`
- Impact: Potential false positives/negatives vs deployed artifact behavior.
- Root cause hypothesis: Local convenience configuration reused in CI.
- Recommendation: Add a preview-mode Playwright config (`vite build && vite preview`) for CI release checks.
- Tradeoffs: Slightly slower E2E startup.
- Migration/compatibility considerations: Keep smoke-dev mode for quick local workflows.
- Test/verification plan: Compare flake/failure rate between dev and preview modes over time.

### Finding B2 - DONE
- Issue: Alembic config emits deprecation warning about missing `path_separator`.
- Evidence:
  - `backend/alembic.ini:1-22` (no `path_separator` key)
  - Warning observed during migration tests in `pytest` output.
- Impact: Future Alembic versions may alter behavior; warning noise persists.
- Root cause hypothesis: Legacy Alembic config format.
- Recommendation: Add `path_separator = os` to Alembic config.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Validate on both macOS/Linux CI.
- Test/verification plan: Re-run migration tests and confirm warning removed.

### Finding B3 - DONE
- Issue: Data generator robustness depends on being executed from repo root.
- Evidence:
  - Relative output paths: `scripts/generate_vehicle_catalog_ts.py:23-26`
- Impact: Operational friction in IDE/CI contexts with different working dirs.
- Root cause hypothesis: Script assumes CWD convention instead of anchoring to repo root.
- Recommendation: Resolve output paths against `REPO_ROOT`.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Keep emitted file locations unchanged.
- Test/verification plan: Add CI step executing generator from non-root CWD.

### Finding B4 - DONE
- Issue: Alembic migration URL conversion relies on string replacement for a narrow set of async driver schemes.
- Evidence:
  - SQLite replacement: `backend/app/db/session.py:61-64`
  - PostgreSQL replacement: `backend/app/db/session.py:66-68`
  - Database URL normalization currently hard-codes `postgresql+asyncpg`: `backend/app/core/config.py:183-218`
- Impact: Future driver changes or non-standard URLs can cause migration startup failures with hard-to-diagnose connection errors.
- Root cause hypothesis: Driver translation is implicit string rewriting instead of explicit scheme mapping.
- Recommendation: Introduce explicit driver mapping/validation table and fail fast with actionable error for unsupported schemes.
- Tradeoffs: Slightly more setup code for stronger portability and diagnostics.
- Migration/compatibility considerations: Preserve current `sqlite+aiosqlite` and `postgresql+asyncpg` behavior by default.
- Test/verification plan: Add unit test matrix for supported/unsupported URL schemes.

### Finding B5 - DONE
- Issue: CI/CD overview omitted the automated Claude PR review workflow.
- Evidence:
  - Workflow present: `.github/workflows/claude-review.yml:1-37`
  - Uses `secrets.ANTHROPIC_API_KEY` and model `claude-sonnet-4-20250514`: `.github/workflows/claude-review.yml:19`, `.github/workflows/claude-review.yml:35-37`
- Impact: Incomplete operational visibility for maintainers reviewing CI behavior and secret dependencies.
- Root cause hypothesis: Documentation lag after workflow addition.
- Recommendation: Document this workflow in repo CI/CD sections (`README`/audit plan) including trigger and secret requirements.
- Tradeoffs: None meaningful.
- Migration/compatibility considerations: Keep workflow optional when secret is absent.
- Test/verification plan: Validate workflow visibility in contributor docs and onboarding checklists.

# Prioritized Backlog
| ID | Title | Impact | Effort | Risk | Owner suggestion | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Centralize calculation runner + replace boolean loading derivation | High | Medium | Medium | frontend | none |
| F2 | Centralize comparison-pair selection policy across result components | High | Medium | Medium | frontend + product | product decision (Q1) |
| S1 | Enforce fail-closed rate limiter in non-development | High | Medium | High | backend/platform | deployment env policy |
| F4 | Graceful fallback on cache JSON corruption | High | Low | Low | backend | none |
| F6 | Add chart-level ErrorBoundary isolation | Medium | Low | Low | frontend | none |
| H3 | Add scenario contract parity checks + remove unchecked key cast | Medium | Medium | Medium | shared/frontend | generator contract check |
| H2 | Expand backend mypy scope incrementally | Medium | Medium | Medium | backend | staged rollout plan |
| T2 | Raise backend coverage floor and add db/session tests | Medium | Medium | Medium | backend | H2 recommended |
| T4 | Add full E2E suite path (nightly/release) | Medium | Low | Low | frontend/platform | CI runtime budget |
| B4 | Harden migration URL driver mapping/validation | Medium | Low | Medium | backend/platform | config scheme policy |
| M1 | Split observability module into focused units | Medium | High | Medium | backend | keep log schema stable |
| M2 + B3 | Anchor generator outputs to `REPO_ROOT` and add CWD test | Medium | Low | Low | shared/scripts | none |
| S2 | Document cookie-auth credential invariants and add config assertions | Low | Low | Low | frontend + backend | deployment docs update |
| P4 | Consume or remove unused autosave `saveStatus` state | Low | Low | Low | frontend | none |
| D1 | Extract shared chart empty-state component | Low | Low | Low | frontend | none |
| T1 | Register pytest marker and clean warning noise | Low | Low | Low | backend | none |
| B2 | Add Alembic `path_separator` config update | Low | Low | Low | backend | none |
| F5 | Replace deprecated HTTP 422 constant usage | Low | Low | Low | backend | none |
| M4 | Move Ruff `per-file-ignores` into `lint` namespace | Low | Low | Low | backend | none |
| M5 | Add or explicitly defer `getSession` API client helper | Low | Low | Low | frontend | API client ownership decision |
| B5 | Document Claude review workflow in CI/CD overview | Low | Low | Low | platform/docs | none |
| D3 | Remove/archive legacy scenario global helpers | Low | Low | Low | data/shared | confirm no external users |

# Migration Plan
- Phase 0: Decision records before behavior changes (blockers)
  - Record Q1 decision for canonical comparison policy (`F2`) and explicit intent for `ComparisonHighlights`.
  - Record Q2 decision for pending session update semantics (`F3`) and backend idempotency expectations.
  - Record Q3 rollout policy for fail-closed rate limiting (`S1`) including emergency override behavior.
  - Record Q5 decision for persisted `results` scope vs UX continuity (`P3`).
- Phase 1: Safety rails and warning cleanup (1-2 sprints)
  - Implement `S1`, `F4`, `T1`, `B2`, `M4`, `F5`.
  - Implement `H3` parity guardrails (contract check + cast hardening).
  - Document credentialed-session invariants (`S2`) and CI/CD workflow inventory (`B5`).
  - Parallelization:
    - Track A (backend safety): `S1` + `F4` + `B2` + `F5`.
    - Track B (tooling/contracts): `T1` + `M4` + `H3`.
    - Track C (docs/config): `S2` + `B5`.
- Phase 2: Low-risk product hardening (1-2 sprints)
  - Implement `F1` orchestration fix and `F6` chart-level error isolation.
  - Implement `D1`, `P4`, `M5`, `M2/B3`, and `B4`.
  - Introduce `test:e2e:full` path and scheduled workflow (`T4`).
  - Parallelization:
    - Track D (frontend correctness): `F1` + `F6` + `D1` + `P4`.
    - Track E (platform/build): `M2/B3` + `B4` + `M5`.
    - Track F (test pipeline): `T4`.
- Phase 3: Structural and policy-heavy changes (2-4 sprints)
  - Implement `F2` policy unification and `F3` update semantics according to Phase 0 decisions.
  - Expand typing/coverage guardrails (`H2` + `T2`).
  - Decompose observability module (`M1`).
  - Optional cleanup: `D3` legacy scenario helpers.
  - Parallelization:
    - Track G (product semantics): `F2` + `F3`.
    - Track H (quality gates): `H2` + `T2`.
    - Track I (platform internals): `M1` (+ `D3` if capacity allows).
- Rollout plan
  - Use feature flags for chart policy and session-update semantics changes.
  - Ship backend hardening first (`S1`/`F4`/`F5`) to reduce operational risk before UI behavior changes.
  - Deploy structural refactors behind telemetry checkpoints (error rate, latency, E2E pass rate).
- Rollback plan
  - Keep compatibility shims for old chart-selection and session-merge behavior for one release window.
  - For backend hardening, allow temporary warning mode (not full fail-closed) behind env toggle.
  - If M1 modularization causes regressions, revert to previous observability wiring while preserving new tests.

## Execution Sequence for Future Codex Sessions
1. Land warnings/guardrails cleanup (`T1`, `B2`, `M4`, `F5`) and cache fallback (`F4`).
2. Land scenario contract hardening (`H3`) and docs/config invariants (`S2`, `B5`).
3. Record and approve behavior-affecting decisions (`Q1`, `Q2`, `Q3`, `Q5`) before implementation.
4. Implement frontend correctness fixes (`F1`, `F6`, `P4`, `D1`) with overlap/error-isolation tests.
5. Implement platform/client hardening (`M2/B3`, `B4`, `M5`) and add full E2E lane (`T4`).
6. Implement policy-heavy changes (`F2`, `F3`), then expand guardrails (`H2`, `T2`), and modularize observability (`M1`) last.

# Tooling and Guardrails Recommendations
- Add `[tool.pytest.ini_options]` marker registration for `enable_redis_cache`.
- Add contract check script: `SCENARIOS.keys()` parity with `ScenarioKey` union.
- Add frontend/runtime guardrail for trusted API origins when credentialed requests are enabled.
- Promote `bandit` into CI using lockfile-synced environment (verify `bandit` version) and start in advisory mode.
- Expand mypy scope with tracked allowlist reductions.
- Raise backend coverage gate progressively and enforce hotspot coverage floor for `backend/app/db/session.py`.
- Add `test:e2e:full` and scheduled workflow; keep PR smoke test for speed.
- `D2` completed by removing unused `runSingle` and mutation-status exports from `useCalculationRunner`; no retention guardrail needed.

# Open Questions / Assumptions

## Q1. Canonical BEV Comparison Policy Across Charts
- Problem: Current charts use different BEV selection logic (`F2`).
- Options:
  1. Compare baseline diesel vs user-selected BEV.
  2. Compare baseline diesel vs lowest-cost BEV automatically.
  3. Show both explicitly with labels.
- Tradeoffs:
  - (1) most user-intent aligned, less “best case” storytelling.
  - (2) strongest advocacy story, but can feel inconsistent with explicit selections.
  - (3) most transparent, highest UI complexity.
- Recommended approach: Option (1) as default, optional “best BEV” badge/secondary metric.

## Q2. Pending Session Update Semantics
- Problem: Existing queueing policy is implicit and order-sensitive (`F3`).
- Options:
  1. Preserve current policy and document as intentional.
  2. Field-level deep merge of pending wizard/results updates.
  3. Serialize updates with monotonically increasing revision numbers.
- Tradeoffs:
  - (1) simplest, highest future ambiguity.
  - (2) balanced, moderate complexity.
  - (3) strongest correctness, biggest implementation surface.
- Recommended approach: Option (2), with tests for ordering and merge precedence.

## Q3. Rate-Limiter Failure Mode in Production
- Problem: Security controls can degrade silently (`S1`).
- Options:
  1. Fail startup when limiter/storage unavailable.
  2. Start with warning-only and emit high-severity alert.
  3. Keep current behavior.
- Tradeoffs:
  - (1) highest security assurance, stricter operations.
  - (2) easier rollout, still risky under attack.
  - (3) least safe.
- Recommended approach: staged rollout from (2) for one release to (1) as default.

## Q4. Scenario Contract Ownership
- Problem: scenario keys are generated from Python but union-typed manually in TS (`H3`).
- Options:
  1. Keep manual union + parity check.
  2. Generate `ScenarioKey` type from Python source.
- Tradeoffs:
  - (1) minimal change, still dual-source maintenance.
  - (2) single-source truth, generator complexity increase.
- Recommended approach: implement (1) immediately, evaluate (2) after stabilization.

## Q5. Local Persistence Scope (`P3`)
- Problem: Removing persisted `results` reduces storage footprint but can regress returning-user UX ("No results yet" after reload).
- Options:
  1. Keep persisting `results` and remove only `vehicleDetails`.
  2. Stop persisting `results` and rely on session resume/refetch.
  3. Persist lightweight result summary and refetch full details when possible.
- Tradeoffs:
  - (1) best UX continuity, higher storage usage.
  - (2) smallest storage footprint, visible UX regression unless resume flow improves.
  - (3) balanced complexity/UX, requires new hydration logic.
- Recommended approach: Option (1) now; revisit Option (3) after session-resume client surface (`M5`) is complete.

## Q6. Assumptions
- No strict external compliance constraints (PII retention/encryption requirements) were provided; recommendations assume standard web-app security baseline.
- Deployment remains Replit autoscale as documented (`docs/replit-deployment-runbook.md:7-15`).

# Appendix
- Commands run
  - `python scripts/validation.py` -> pass.
  - `python -m ruff check data backend scripts tests` -> pass, Ruff config deprecation warning.
  - `python -m black --check data backend scripts tests` -> pass.
  - `python -m isort --check-only data backend scripts tests` -> fail on `tests/test_config.py`.
  - `python -m mypy backend/app/core backend/app/api backend/app/main.py` -> pass.
  - `python -m pytest tests --cov` -> 77 passed; warnings for pytest marker, Alembic deprecation, HTTP 422 constant deprecation; total coverage 88%.
  - `cd frontend && bun run lint` -> pass.
  - `cd frontend && bun run typecheck` -> pass.
  - `cd frontend && bun run test` -> 220 passed.
  - `cd frontend && bun run test:e2e` -> initially failed due missing browser, passed after `cd frontend && bunx playwright install chromium`.
  - `python -m pip_audit -r requirements.lock.txt --strict` -> no known vulnerabilities.
  - `python -m pip_audit -r requirements-dev.lock.txt --strict` -> no known vulnerabilities.
  - `python -m pip show bandit` -> local env had `bandit==1.7.0` (drift from lockfile).
  - `python -m pip index versions bandit` -> `bandit==1.9.3` exists and is current.
  - `python - <<...>>` (Starlette status constant check) -> `HTTP_422_UNPROCESSABLE_ENTITY` emits deprecation warning and `HTTP_422_UNPROCESSABLE_CONTENT` is available.
  - `cd frontend && bun audit --audit-level=high` -> no vulnerabilities.
  - `cd frontend && bun pm untrusted` -> 0 untrusted dependencies with scripts.
  - `python -m vulture backend data scripts tests --min-confidence 80` -> one unused var in tests.
  - `python -m bandit -r backend data scripts -q` -> failed in local env due stale install path (`pbr` import error under old `bandit`).
- Notes
  - This report is evidence-based from repository contents and executed commands in this session.
  - Where behavior is ambiguous by design (`F3`, `F2`), recommendations are framed as explicit decisions to make.
- Additional references
  - `.github/workflows/ci.yml`
  - `.github/workflows/dependency-audit.yml`
  - `.github/workflows/data-sync-check.yml`
  - `.github/workflows/claude-review.yml`
  - `backend/app/core/security.py`
  - `backend/app/core/cache.py`
  - `backend/app/core/observability.py`
  - `frontend/src/hooks/useCalculations.ts`
  - `frontend/src/services/sessionLifecycle.ts`
  - `shared/calculator/tcoCalculator.ts`
