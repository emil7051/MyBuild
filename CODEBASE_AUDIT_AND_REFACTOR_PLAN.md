**Executive Summary**
- Session access-control secrets were removed by design; docs/tests now align with sessionId-only access. This increases the importance of keeping session payloads free of sensitive data or adding access control later. Evidence: `SECURITY.md`, `tests/test_api.py`.
- Validation ranges for vehicle overrides were unified to the calculator via shared `OVERRIDE_LIMITS` in `data/constants.py`. Evidence: `data/constants.py`, `frontend/src/forms/wizardForm.ts`, `backend/app/models/calculation.py`, `shared/data/constants.generated.ts`.
- Session creation is duplicated across autosave and calculation flows, each with its own mutex, which can create duplicate sessions and inconsistent persistence under race conditions. Evidence: `frontend/src/hooks/useWizardAutosave.ts:63`, `frontend/src/hooks/useCalculations.ts:68`.
- Analytics aggregation currently loads all calculation rows and performs in-memory aggregation, which will not scale with growing usage. Evidence: `backend/app/services/sessions.py:210`, `backend/app/services/sessions.py:220`.
- Several dead or unused elements (session secret helpers, unused frontend API functions, unused Python deps) add maintenance risk and suggest incomplete refactors. Evidence: `backend/app/core/security.py:95`, `frontend/src/services/api.ts:17`, `requirements.txt:20`.

**Progress Update (2026-02-05)**
Completed:
- Session secret enforcement removed by design: tests/docs aligned to sessionId-only access; `SECURITY.md` updated to reflect no per-session secret and localStorage usage.
- Override validation ranges unified to the calculator via shared `OVERRIDE_LIMITS` in `data/constants.py`; frontend and backend now consume the same limits; shared constants regenerated.
- Analytics UI removed from frontend (unused components/hooks deleted and API client call removed).
- Analytics endpoint now requires `ANALYTICS_API_KEY`; if unset, endpoint is disabled (403). Tests and docs updated accordingly.

Remaining (highest-impact):
- Centralize session lifecycle to prevent duplicate session creation (CR-01).
- Optimize analytics aggregation path (PERF-01).
- Cache-first session lookup and Redis reconnection strategy (CR-02, CR-03).
- Make migrations an explicit deploy step (CR-04).
- Remove remaining dead code/deps and resolve dual lockfile strategy (DEAD-02/03, DEP-01).

**Repo Overview**
Architecture map and data flow:
- Frontend SPA (React + Vite + Bun). Entry: `frontend/src/main.tsx`. Routes: `frontend/src/App.tsx`. Evidence: `README.md:28`, `README.md:102`, `frontend/package.json:7`.
- Shared calculator (TypeScript). Core: `shared/calculator/tcoCalculator.ts`, math: `shared/calculator/math.ts`. Evidence: `README.md:110`, `shared/calculator/tcoCalculator.ts:1`.
- Backend API (FastAPI). Entry: `backend/app/main.py`, routes: `backend/app/api/router.py`. Evidence: `README.md:94`, `backend/app/main.py:1`.
- Data source of truth (Python): `data/` with generator `scripts/generate_vehicle_catalog_ts.py` feeding `shared/data/*`. Evidence: `README.md:83`, `README.md:114`.
- Persistence: PostgreSQL via SQLAlchemy models in `backend/app/db/models.py`, caching via Redis in `backend/app/core/cache.py`. Evidence: `README.md:21`, `backend/app/db/models.py:1`.
- CI: GitHub Actions workflows in `.github/workflows/ci.yml` and `.github/workflows/dependency-audit.yml`. Evidence: `.github/workflows/ci.yml:1`, `.github/workflows/dependency-audit.yml:1`.

Key entry points and runtime boundaries:
- Backend app factory and middleware: `backend/app/main.py`.
- API routes: `backend/app/api/router.py`.
- Frontend boot: `frontend/src/main.tsx`.
- Shared calc entry: `shared/calculator/index.ts` and `shared/calculator/tcoCalculator.ts`.

Dependency map (high-level):
- FastAPI + SQLAlchemy + Alembic + Redis + slowapi from `requirements.txt`. Evidence: `requirements.txt:9`.
- React + React Query + Zod + Zustand from `frontend/package.json`. Evidence: `frontend/package.json:16`.

Baseline health snapshot:
- CI lint/test coverage is defined in `.github/workflows/ci.yml` with a backend coverage floor at 50%. Evidence: `.github/workflows/ci.yml:68`.
- Dependency audits are performed weekly and on PRs. Evidence: `.github/workflows/dependency-audit.yml:1`.
- I did not run tests or linters locally; see Appendix for commands run and limitations.

Constraints (not provided, treated as assumptions):
- Target runtime/platform(s): Not specified.
- Languages/frameworks: Python/FastAPI, TypeScript/React/Vite, SQLAlchemy, Redis. Evidence: `README.md:127`, `README.md:140`.
- Deployment environment(s): Not specified.
- Performance/SLO constraints: Not specified.
- Security/compliance constraints: Not specified.
- Backward compatibility requirements: Not specified.
- “Do not touch” areas: Not specified.
- Timeline / available engineering capacity: Not specified.
- Preferred coding standards/linting rules: See CI lint tools. Evidence: `.github/workflows/ci.yml:35`.

**Top Risks & Hotspots**
| Rank | Risk | Likelihood | Impact | Score | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Session access is unauthenticated; avoid storing sensitive data or add access control | 3 | 4 | 12 | `backend/app/api/router.py`, `SECURITY.md` |
| 2 | Duplicate session creation paths can race | 3 | 4 | 12 | `frontend/src/hooks/useWizardAutosave.ts:63`, `frontend/src/hooks/useCalculations.ts:68` |
| 3 | Analytics aggregation loads full table in memory | 3 | 4 | 12 | `backend/app/services/sessions.py:210`, `backend/app/services/sessions.py:220` |
| 4 | Cache doesn’t avoid the first DB hit | 3 | 3 | 9 | `backend/app/services/sessions.py:127` |
| 5 | Rate limiting likely per-process only (slowapi default storage) | 3 | 3 | 9 | `backend/app/core/security.py:85` |
| 6 | Migrations run on app startup (multi-instance risk) | 2 | 4 | 8 | `backend/app/db/session.py:37` |
| 7 | Redis client initialized once; no retry if Redis unavailable | 3 | 2 | 6 | `backend/app/core/cache.py:16` |
| 8 | Unused deps and dead code increase surface area | 3 | 2 | 6 | `requirements.txt:20`, `backend/app/core/security.py:95` |
| 9 | Dual lockfile strategy can drift | 2 | 3 | 6 | `frontend/bun.lock`, `frontend/package-lock.json`, `.github/workflows/dependency-audit.yml:90` |

**Findings**
**Correctness & Reliability**

**CR-01 — Duplicate session creation paths can race**
Issue: Session creation is implemented in both autosave and calculation flows with separate mutexes, which can create multiple sessions if both trigger before `sessionId` is set.
Evidence:
- `frontend/src/hooks/useWizardAutosave.ts:63` shows `createSession` in autosave with `isCreatingSessionRef` local to that hook.
- `frontend/src/hooks/useCalculations.ts:68` shows `createSession` in the calculation flow with a different `isCreatingSession` ref.
Impact: Duplicate sessions, inconsistent server state, and user confusion on resume. In worst cases, session updates may apply to a session that is not the one referenced by local storage.
Root cause hypothesis: Session lifecycle management is spread across multiple hooks without a shared single-flight mechanism.
Recommendation: Centralize session lifecycle in a single store/service layer (e.g., Zustand action) and ensure a single shared mutex for creation/update. One path should own `createSession`, others should enqueue updates.
Tradeoffs: Centralization introduces refactor risk and must be coordinated with existing hooks to avoid regressions.
Migration/compatibility considerations: Preserve API contracts and ensure `sessionId` semantics remain stable. Provide a transitional adapter to route old hook calls to the new service.
Test/verification plan: Add a concurrency test that simulates autosave + calculation triggering back-to-back and asserts only one session is created and all updates land on that ID.

**CR-02 — Cache doesn’t avoid the first DB hit**
Issue: `get_session` performs a database lookup before checking Redis cache, reducing cache benefit.
Evidence:
- `backend/app/services/sessions.py:127` fetches the DB record before cache lookup at `backend/app/services/sessions.py:131`.
Impact: Additional DB load under read-heavy traffic; Redis cache only saves secondary queries.
Root cause hypothesis: Cache introduced after DB existence check to preserve “not found” errors.
Recommendation: Check Redis first and fall back to DB only on cache miss, or cache a short-lived “not found” marker. Alternatively, query DB only for existence and cached payload separately.
Tradeoffs: Cache-first can return stale data if cache invalidation fails; mitigated by TTL and update-on-write.
Migration/compatibility considerations: No API schema changes; ensure cache entries include a version or updated_at to detect staleness.
Test/verification plan: Add tests for cache hit path and stale cache invalidation by updating a session and ensuring cache refresh.

**CR-03 — Redis client initialization is one-shot**
Issue: Redis client is created at import time and not reinitialized after failure.
Evidence:
- `backend/app/core/cache.py:16` creates the client; if creation fails it returns None and remains None for process lifetime.
Impact: If Redis is temporarily unavailable at startup, caching remains disabled even after Redis recovers.
Root cause hypothesis: Simplified init logic without reconnection strategy.
Recommendation: Lazy-initialize client on first use and/or retry with exponential backoff. Store a function that can recreate the client if `redis_client` is None.
Tradeoffs: Slight overhead in hot path to check/reconnect; can be minimized with a lock and backoff.
Migration/compatibility considerations: No API changes; ensure reconnection logic is thread-safe in async context.
Test/verification plan: Unit test that simulates a failed connection followed by a successful retry, verifying cache usage.

**CR-04 — Migrations run on app startup**
Issue: Alembic migrations execute during app startup.
Evidence:
- `backend/app/db/session.py:37` runs `command.upgrade` at startup.
Impact: Startup latency and potential conflicts if multiple instances start concurrently; in some deployments this can block readiness or cause migration race errors.
Root cause hypothesis: Convenience for dev environments baked into runtime init.
Recommendation: Make migrations an explicit deployment step (CI/CD job, release hook). Gate runtime migrations behind a config flag.
Tradeoffs: Requires operational discipline; reduces “it just works” dev simplicity.
Migration/compatibility considerations: Ensure dev workflow still runs migrations easily (e.g., `make migrate`).
Test/verification plan: Add integration test that asserts startup with `RUN_MIGRATIONS=false` does not attempt migrations.

**CR-05 — Broad exception swallowing in secret verification**
Issue: `verify_secret` catches all exceptions and silently returns False.
Evidence:
- `backend/app/core/security.py:127` catches `Exception` and returns False.
Impact: Real operational errors (e.g., bcrypt failures) are hidden, reducing observability and complicating debugging.
Root cause hypothesis: Defensive programming to avoid crashes, without structured logging.
Recommendation: Catch specific exceptions and log at warning level; treat unexpected errors as 500 to avoid false negatives.
Tradeoffs: More visible errors may surface but provide clarity; can be feature-flagged in production.
Migration/compatibility considerations: If callers expect boolean-only behavior, introduce logging first then tighten error handling.
Test/verification plan: Add a unit test that simulates bcrypt failure and asserts logging/exception path.

**Security & Privacy**

**SEC-01 — Session access-control secret removed by design**
Issue: Session secret access control was previously documented/tested but is not enforced in the API.
Status (2026-02-05): Resolved by aligning tests/docs to sessionId-only access. The API no longer returns or validates a session secret; the privacy posture now depends on keeping session payloads non-sensitive or adding access control later.
Evidence:
- Session endpoints do not require `X-Session-Secret` in `backend/app/api/router.py`.
- `SECURITY.md` updated to reflect sessionId-only access and localStorage usage.
- Session secret tests removed from `tests/test_security.py` and `tests/test_api.py`.
Remaining considerations:
- Decide whether to remove `session_secret_hash` column and helper functions (see DEAD-01).
- If PII is required in sessions, introduce real access control.

**SEC-02 — Session ID stored in localStorage**
Issue: Session ID is persisted to localStorage; this is acceptable only if session payloads are non-sensitive.
Status (2026-02-05): Security guidance updated to explicitly allow sessionId persistence in localStorage, with the caveat that no PII should be stored client-side.
Evidence:
- Store persistence uses localStorage in `frontend/src/state/tcoStore.ts:77`.
- `SECURITY.md` updated to reflect localStorage usage.
Follow-up: If session payloads ever include sensitive data, revisit HttpOnly cookie-based access or other auth.

**SEC-03 — Analytics access now server-side only**
Issue: Backend allowed optional API key enforcement while frontend attempted to call the endpoint without a key.
Status (2026-02-05): Analytics UI removed; analytics endpoint now requires `ANALYTICS_API_KEY` and is disabled if unset. This keeps analytics data private and backend-only.
Evidence:
- `frontend/src/components/results/AnalyticsSummaryCard.tsx` and `frontend/src/hooks/useAnalyticsSummary.ts` removed.
- `backend/app/core/security.py` requires the key; tests updated in `tests/test_security.py`.
Follow-up: If internal review is needed, add an admin-only UI or a secured reporting workflow.

**SEC-04 — Rate limiting likely per-process only (assumption)**
Issue: slowapi limiter is instantiated without an explicit shared storage backend.
Evidence:
- Limiter is created with `Limiter(key_func=get_client_ip)` in `backend/app/core/security.py:85` with no storage configured.
Impact: If slowapi defaults to in-memory storage (assumption), rate limiting will be per-process and ineffective across multiple workers or instances.
Root cause hypothesis: Simple default configuration used for local dev.
Recommendation: Configure slowapi with Redis storage and document it in `Settings`, or ensure a single-process deployment.
Tradeoffs: Requires Redis availability and configuration; adds operational dependencies.
Migration/compatibility considerations: For multi-instance deployments, configure shared storage before scaling out.
Test/verification plan: Add a test that asserts configured storage type from settings when rate limiting is enabled.

**Performance**

**PERF-01 — Analytics aggregation loads all calculation rows into memory**
Issue: Analytics summary reads all calculation results and aggregates in Python.
Evidence:
- `backend/app/services/sessions.py:210` selects all rows and `backend/app/services/sessions.py:220` builds a `session_map` in memory.
Impact: Memory growth and latency as data volume increases; analytics endpoint can become a hotspot.
Root cause hypothesis: Initial optimization focused on fewer columns but still full-table read.
Recommendation: Move aggregation to SQL (group-by per session/vehicle), or precompute aggregates in a materialized table. Consider background aggregation jobs.
Tradeoffs: SQL complexity or additional storage for precomputed metrics.
Migration/compatibility considerations: Validate parity between old and new aggregation outputs; consider dual-run for a release to compare results.
Test/verification plan: Add a performance regression test with a large dataset and compare response times; verify correctness with fixtures.

**Maintainability**

**MAINT-01 — Validation ranges drift across layers**
Issue: Override bounds were inconsistent across frontend Zod schema, backend Pydantic, and calculator clamps.
Status (2026-02-05): Resolved by centralizing limits in `data/constants.py` (`OVERRIDE_LIMITS`) and consuming them in frontend/backend; shared constants regenerated.
Evidence:
- `data/constants.py` defines `OVERRIDE_LIMITS`.
- `frontend/src/forms/wizardForm.ts` and `backend/app/models/calculation.py` now use those limits.
- Calculator remains the canonical clamp source in `shared/calculator/tcoCalculator.ts`.
Follow-up: Add a CI parity check to ensure limits remain aligned across layers.

**MAINT-02 — Comment/code mismatch in duty-cycle validation**
Issue: A comment claims validation includes sum check, but the function does not check the sum.
Evidence:
- Comment in `frontend/src/state/tcoStore.ts:241` references sum validation, while `validateDutyCycle` only checks NaN/negative/out-of-range in `frontend/src/state/tcoStore.ts:97`.
Impact: Misleads maintainers and can lead to incorrect assumptions in future refactors.
Root cause hypothesis: Comment updated without aligning behavior.
Recommendation: Update the comment or implement a sum check consistent with the comment, and add a unit test.
Tradeoffs: Adding sum checks may change current UX; updating comment is lower risk.
Migration/compatibility considerations: If behavior changes, update any UI validation messaging accordingly.
Test/verification plan: Add unit tests that assert expected behavior with sums not equal to 100.

**MAINT-03 — Duplicate payload sanitization logic**
Issue: Overrides sanitization is re-implemented in multiple places.
Evidence:
- `frontend/src/hooks/useWizardAutosave.ts:9` sanitizes overrides locally.
- `frontend/src/utils/payload.ts:9` provides similar sanitization for session payloads.
Impact: Risk of drift and inconsistent behavior across flows.
Root cause hypothesis: Utility functions were not reused.
Recommendation: Export and reuse a single sanitizer function across hooks.
Tradeoffs: Small refactor; low risk.
Migration/compatibility considerations: Ensure output remains identical to avoid behavioral changes.
Test/verification plan: Add a unit test for sanitizer and use in both paths.

**Duplication & Dead Code**

**DEAD-01 — Session secret helpers and DB column unused**
Issue: Session secret functions and schema exist but are not wired into API flow.
Evidence:
- Helpers in `backend/app/core/security.py:95` are unused.
- `session_secret_hash` column in `backend/app/db/models.py:46` is unused by services.
Impact: Increases cognitive load and creates false sense of security.
Root cause hypothesis: Feature partially implemented then stalled.
Recommendation: Either complete the feature (see SEC-01) or remove the unused helpers and column to reduce confusion.
Tradeoffs: Removing the column requires a migration; implementing requires frontend changes.
Migration/compatibility considerations: If removing, provide a migration and update tests/docs accordingly.
Test/verification plan: Add tests to ensure the chosen path (implemented or removed) is consistent.

**DEAD-02 — Unused frontend API calls**
Issue: `fetchVehicles` and `fetchVehicle` are defined but unused; frontend uses static shared data instead.
Evidence:
- API calls in `frontend/src/services/api.ts:17` are not referenced anywhere else (confirmed via search).
- Vehicle data is consumed from shared catalog in `frontend/src/hooks/useVehicleCatalog.ts:4`.
Impact: Dead code increases maintenance overhead and creates ambiguity about source-of-truth.
Root cause hypothesis: Backend endpoints exist for other clients but frontend no longer uses them.
Recommendation: Remove unused functions or re-enable API consumption with a clear product reason.
Tradeoffs: Removing may affect future integrations; keeping requires documentation.
Migration/compatibility considerations: Ensure any external clients rely on backend endpoints are documented separately.
Test/verification plan: If removed, update any tests that mock these APIs.

**DEAD-03 — Unused Python dependencies**
Issue: Several runtime dependencies appear unused by repo code.
Evidence:
- `requirements.txt:20` includes `orjson`, but there are no code references.
- `requirements.txt:48` includes `marshmallow` and `cerberus`, with no references found.
- `requirements.txt:58` includes `loguru`, with no references found.
Impact: Increased attack surface, longer install times, and maintenance overhead.
Root cause hypothesis: Dependencies carried over from previous tooling or experiments.
Recommendation: Remove unused dependencies or document their use. Consider a dependency usage check in CI.
Tradeoffs: Removing may break out-of-repo tooling; verify before deletion.
Migration/compatibility considerations: Validate scripts in `scripts/` still run after removal.
Test/verification plan: Run `pipdeptree` or `python -m vulture` in CI to confirm usage.

**Dependency Health**

**DEP-01 — Dual lockfiles and audit generation may drift**
Issue: `frontend` has both `bun.lock` and `package-lock.json`, and CI regenerates a package-lock for npm audit.
Evidence:
- Lockfiles present: `frontend/bun.lock` and `frontend/package-lock.json`.
- CI generates `package-lock.json` for npm audit in `.github/workflows/dependency-audit.yml:90`.
Impact: Potential mismatch between audited dependency tree and actual Bun install tree.
Root cause hypothesis: npm audit requirement forced a separate lockfile.
Recommendation: Choose a single source of truth for lockfile. Option A: keep `bun.lock` and generate package-lock in CI only (remove committed package-lock). Option B: use npm/pnpm lockfile exclusively and align installs.
Tradeoffs: npm audit tooling expects package-lock; Bun-based installs prefer bun.lock.
Migration/compatibility considerations: If removing package-lock, update `.gitignore` and CI scripts accordingly.
Test/verification plan: Verify that dependency audit still works and reproducible builds remain stable.

**Tests & Observability**

**TEST-01 — Tests expect session secret that API does not implement**
Issue: Security tests assert session secret behavior that is absent in the current API.
Evidence:
- Tests in `tests/test_security.py:149` assert `sessionSecret` in response and enforce `X-Session-Secret`.
- API routes do not include secret validation in `backend/app/api/router.py:77`.
Impact: Either tests are failing or the code has drifted from its intended security design, reducing confidence.
Root cause hypothesis: Feature partially removed or never completed.
Recommendation: Resolve by implementing the feature or updating tests/docs to reflect current behavior.
Tradeoffs: Implementation introduces client-side handling; removal reduces security posture.
Migration/compatibility considerations: Ensure documentation and client behavior is updated to match.
Test/verification plan: Align CI to the chosen behavior and ensure tests pass.

**TEST-02 — Backend coverage floor is low**
Issue: CI allows backend coverage down to 50%.
Evidence:
- Coverage gate configured at `--cov-fail-under=50` in `.github/workflows/ci.yml:74`.
Impact: Important regressions can slip without test detection.
Root cause hypothesis: Initial threshold set to accommodate legacy code.
Recommendation: Raise the threshold incrementally (e.g., 50 → 60 → 70) with a focused test backlog.
Tradeoffs: Higher thresholds may slow delivery initially.
Migration/compatibility considerations: Increase only after adding tests for critical paths.
Test/verification plan: Track coverage trend and fail CI at the new threshold.

**Build/Deploy Ergonomics**

**OPS-01 — `docker-compose` runs backend with `--reload`**
Issue: Compose runs Uvicorn with reload enabled.
Evidence:
- `docker-compose.yml:7` uses `uvicorn ... --reload`.
Impact: Fine for dev, but if used in production it is unsafe and inefficient.
Root cause hypothesis: Single compose file used for dev and production.
Recommendation: Split dev and prod compose files or guard reload with an env flag.
Tradeoffs: Extra config overhead.
Migration/compatibility considerations: Maintain a `docker-compose.prod.yml` or documented prod run command.
Test/verification plan: Verify production startup uses a non-reload configuration.

**AI-Generated Pattern Indicators (Symptoms, Not Blame)**

**AI-01 — Over-defensive validation scattered across layers**
Issue: The same override validation is repeated in three layers with inconsistent bounds.
Evidence:
- Frontend Zod validation in `frontend/src/forms/wizardForm.ts:112`.
- Backend Pydantic validation in `backend/app/models/calculation.py:89`.
- Calculator clamping in `shared/calculator/tcoCalculator.ts:211`.
Impact: Divergent behavior, silent clamps, and maintenance cost. This is typical of “defensive duplication” in AI-assisted code.
Root cause hypothesis: Each layer independently added safety checks instead of centralizing constraints.
Recommendation: Replace with a shared, generated constraint catalog used by all layers.
Tradeoffs: Cross-layer refactor with coordination overhead.
Migration/compatibility considerations: Ensure backward compatibility with existing persisted data.
Test/verification plan: Add constraint parity tests across frontend/backend/calculator.

**AI-02 — Error swallowing without observability**
Issue: Broad exception handling hides failures in cache and secret verification.
Evidence:
- `backend/app/core/cache.py:43` catches `Exception` and logs a warning.
- `backend/app/core/security.py:127` catches `Exception` and returns False with no logging.
Impact: Failures become silent, making production issues difficult to diagnose.
Root cause hypothesis: Auto-generated defensive patterns without structured error strategy.
Recommendation: Replace with narrow exception handling and structured logging; consider metrics.
Tradeoffs: More logs; ensure rate-limited logging to avoid noise.
Migration/compatibility considerations: Introduce logging first, then tighten exception scopes.
Test/verification plan: Add tests to assert logging for error paths.

**AI-03 — Comment drift from behavior**
Issue: Comment claims sum validation that the implementation does not perform.
Evidence:
- `frontend/src/state/tcoStore.ts:241` comment vs `frontend/src/state/tcoStore.ts:97` behavior.
Impact: Misleads reviewers and indicates a likely copy/paste or auto-generated doc artifact.
Root cause hypothesis: Automated or copy/paste documentation without verification.
Recommendation: Align comments to actual behavior or implement the described check.
Tradeoffs: Minimal.
Migration/compatibility considerations: None.
Test/verification plan: Update unit tests to lock intended behavior.

**Prioritized Backlog**
| ID | Title | Impact | Effort | Risk | Owner Suggestion | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Remove session secret access control (Done) | High | Medium | Medium | Backend + Frontend | SEC-01 decision |
| P2 | Unify override constraints across layers (Done) | High | Medium | Medium | Shared + Frontend + Backend | MAINT-01 |
| P3 | Centralize session lifecycle (single-flight creation) | High | Medium | Medium | Frontend | CR-01 |
| P4 | Optimize analytics aggregation | High | High | Medium | Backend + Data | PERF-01 |
| P5 | Confirm localStorage policy and avoid PII in sessions (Done) | High | Medium | Medium | Frontend + Backend | SEC-02 |
| P6 | Add Redis-backed rate limit storage | Medium | Medium | Low | Backend/Infra | SEC-04 |
| P7 | Make migrations an explicit deploy step | Medium | Medium | Low | Backend/Infra | CR-04 |
| P8 | Remove unused deps and dead code | Medium | Low | Low | Backend + Frontend | DEAD-02, DEAD-03 |
| P9 | Resolve dual lockfile strategy | Medium | Low | Low | Frontend/Infra | DEP-01 |
| P10 | Raise backend coverage threshold incrementally | Medium | Medium | Low | Backend | TEST-02 |

**Migration Plan**
1. Phase 1 — Safety rails and alignment.
Add parity tests for override constraints, add a session lifecycle unit test to prevent duplicate session creation, and add a security regression test for sessionId-only access. Rollout: merge behind feature flags where applicable. Rollback: revert to current behavior by disabling flags.
2. Phase 2 — Low-risk refactors.
Centralize override sanitization, remove unused frontend API calls, remove unused dependencies after verifying no scripts use them, and adjust cache initialization to be lazy. Rollout: small PRs with targeted tests. Rollback: revert per PR if regressions occur.
3. Phase 3 — High-impact structural changes.
Move migrations to a deploy-time step, and optimize analytics aggregation (potentially adding new tables or jobs). Rollout: staged deployment with dual-read for analytics. Rollback: feature-flag enforcement and keep backward compatibility for legacy sessions during the transition.

**Tooling & Guardrails Recommendations**
- Add a CI check that validates override constraint parity across frontend, backend, and calculator.
- Add vulture (already in dev deps) to CI for unused Python code detection and a similar ESLint rule for unused exports.
- Add a check that ensures session secret behavior aligns with tests/docs (single source of truth).
- Add a performance budget test for analytics endpoint with a fixture dataset.
- Add a dependency usage audit (pipdeptree + grep) before pruning dependencies.

**Open Questions / Assumptions**
- Session secrets are no longer enforced by design; should we remove the unused `session_secret_hash` column and related helpers entirely?
- Analytics access is server-side only (API key required); do we want an internal/admin UI or a separate reporting workflow to view analytics?
- Are there multi-instance deployments where rate limiting must be shared? (Assumption for SEC-04.)
- Should sessions be resumable across browsers/devices, and what is the privacy requirement for stored operator contact emails (given sessionId-only access)?

**Appendix**
Commands run (local, read-only):
- `rg --files`
- `sed -n '1,200p' README.md`
- `nl -ba backend/app/main.py | sed -n '1,260p'`
- `nl -ba backend/app/core/security.py | sed -n '1,260p'`
- `nl -ba backend/app/core/middleware.py | sed -n '1,260p'`
- `nl -ba backend/app/api/router.py | sed -n '1,260p'`
- `nl -ba backend/app/services/sessions.py | sed -n '1,320p'`
- `nl -ba backend/app/core/cache.py | sed -n '1,220p'`
- `nl -ba backend/app/db/models.py | sed -n '1,260p'`
- `nl -ba backend/app/models/session.py | sed -n '1,320p'`
- `nl -ba backend/app/models/calculation.py | sed -n '1,260p'`
- `nl -ba frontend/src/services/api.ts | sed -n '1,260p'`
- `nl -ba frontend/src/hooks/useWizardAutosave.ts | sed -n '1,260p'`
- `nl -ba frontend/src/hooks/useCalculations.ts | sed -n '1,260p'`
- `nl -ba frontend/src/state/tcoStore.ts | sed -n '1,260p'`
- `nl -ba frontend/src/forms/wizardForm.ts | sed -n '1,260p'`
- `nl -ba shared/calculator/tcoCalculator.ts | sed -n '190,270p'`
- `nl -ba tests/test_security.py | sed -n '1,520p'`
- `nl -ba requirements.txt | sed -n '1,220p'`
- `nl -ba .github/workflows/ci.yml | sed -n '40,140p'`
- `nl -ba .github/workflows/dependency-audit.yml | sed -n '50,170p'`
- `rg -n "fetchVehicles|fetchVehicle" frontend/src`
- `rg -n "generate_session_secret|hash_secret|verify_secret" backend`
- `rg -n "marshmallow|cerberus" -S .`
- `rg -n "dotenv" backend scripts`
- `rg -n "dangerouslySetInnerHTML|innerHTML|document.write|window.location|localStorage|sessionStorage" frontend/src`
- `git log -n 20 --oneline`
- `git show --stat 4ee9f16`
- `git show --stat 7897eac`
- `rg -n "Session Secret|X-Session-Secret|session secret|secret" tests/test_security.py`
- `rg -n "Analytics-Key|analytics key" backend/app/core/security.py backend/app/api/router.py frontend/src/services/api.ts`
- `rg -n "analytics" backend frontend shared tests`
- `rg -n "contactEmail|operatorProfile" frontend/src`
- `rg -n "override" shared/calculator/tcoCalculator.ts`
- `python scripts/generate_vehicle_catalog_ts.py`

Notes:
- No tests or linters were executed in this audit; findings are based on static inspection.
- Items marked as assumptions require runtime or deployment context to verify.
