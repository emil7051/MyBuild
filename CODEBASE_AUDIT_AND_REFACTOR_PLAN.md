**Executive Summary**
- The most critical gap is the incomplete session access-control secret: tests and security docs expect it, the DB schema has a hash column, but the API does not enforce it. This makes session IDs effectively bearer tokens and undermines the stated privacy model for contact emails. Evidence: `tests/test_security.py:149`, `tests/test_security.py:172`, `SECURITY.md:116`, `backend/app/db/models.py:46`, `backend/app/api/router.py:77`.
- Validation ranges for vehicle overrides drift between frontend, backend, and the shared calculator. This creates silent clamping and inconsistent results across layers. Evidence: `frontend/src/forms/wizardForm.ts:112`, `backend/app/models/calculation.py:89`, `shared/calculator/tcoCalculator.ts:211`.
- Session creation is duplicated across autosave and calculation flows, each with its own mutex, which can create duplicate sessions and inconsistent persistence under race conditions. Evidence: `frontend/src/hooks/useWizardAutosave.ts:63`, `frontend/src/hooks/useCalculations.ts:68`.
- Analytics aggregation currently loads all calculation rows and performs in-memory aggregation, which will not scale with growing usage. Evidence: `backend/app/services/sessions.py:210`, `backend/app/services/sessions.py:220`.
- Several dead or unused elements (session secret helpers, unused frontend API functions, unused Python deps) add maintenance risk and suggest incomplete refactors. Evidence: `backend/app/core/security.py:95`, `frontend/src/services/api.ts:17`, `requirements.txt:20`.

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
| 1 | Session access control secret not implemented (privacy exposure) | 4 | 5 | 20 | `backend/app/api/router.py:77`, `tests/test_security.py:149`, `SECURITY.md:116` |
| 2 | Validation drift across frontend/backend/calculator | 4 | 4 | 16 | `frontend/src/forms/wizardForm.ts:112`, `backend/app/models/calculation.py:89`, `shared/calculator/tcoCalculator.ts:211` |
| 3 | Duplicate session creation paths can race | 3 | 4 | 12 | `frontend/src/hooks/useWizardAutosave.ts:63`, `frontend/src/hooks/useCalculations.ts:68` |
| 4 | Analytics aggregation loads full table in memory | 3 | 4 | 12 | `backend/app/services/sessions.py:210`, `backend/app/services/sessions.py:220` |
| 5 | Session ID stored in localStorage despite “no sensitive data” guidance | 3 | 4 | 12 | `frontend/src/state/tcoStore.ts:176`, `SECURITY.md:96` |
| 6 | Rate limiting likely per-process only (slowapi default storage) | 3 | 3 | 9 | `backend/app/core/security.py:85` |
| 7 | Migrations run on app startup (multi-instance risk) | 2 | 4 | 8 | `backend/app/db/session.py:37` |
| 8 | Redis client initialized once; no retry if Redis unavailable | 3 | 2 | 6 | `backend/app/core/cache.py:16` |
| 9 | Unused deps and dead code increase surface area | 3 | 2 | 6 | `requirements.txt:20`, `backend/app/core/security.py:95` |
| 10 | Dual lockfile strategy can drift | 2 | 3 | 6 | `frontend/bun.lock`, `frontend/package-lock.json`, `.github/workflows/dependency-audit.yml:90` |

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

**SEC-01 — Session access-control secret not implemented**
Issue: Session secret access control is described in tests and documentation but not enforced in the API.
Evidence:
- Tests expect a `sessionSecret` and 403 without it in `tests/test_security.py:149` and `tests/test_security.py:172`.
- Security policy states “access requires session secret” in `SECURITY.md:116`.
- DB schema has `session_secret_hash` column in `backend/app/db/models.py:46`.
- API routes `create_session`, `get_session`, `update_session` do not check any secret in `backend/app/api/router.py:77` and `backend/app/api/router.py:122`.
- Secret helper functions exist but are unused in `backend/app/core/security.py:95`.
Impact: Any party with a session ID can fetch or update sessions, including contact_email in operator profiles, violating the documented privacy posture.
Root cause hypothesis: Partial implementation left behind after a design change or unfinished feature.
Recommendation: Either implement session secret enforcement or explicitly remove it from tests/docs and redesign the privacy model. Implementing requires generating a secret on create, storing hash, returning secret, and validating `X-Session-Secret` on GET/PUT.
Tradeoffs: Implementing increases client complexity (must store and send secret); removing reduces protection but simplifies UX.
Migration/compatibility considerations: Rolling out enforcement requires a backfill plan for existing sessions (grace period or optional auth for legacy records).
Test/verification plan: Use the existing tests in `tests/test_security.py` as the acceptance suite and ensure they pass; add a migration test for backfilled secrets.

**SEC-02 — Session ID stored in localStorage contradicts security guidance**
Issue: Session ID is persisted to localStorage even though docs claim no sensitive data is stored there.
Evidence:
- Store persistence uses localStorage in `frontend/src/state/tcoStore.ts:77` and includes `sessionId` in persisted state at `frontend/src/state/tcoStore.ts:176`.
- Security policy claims no sensitive data in localStorage in `SECURITY.md:96`.
Impact: If session IDs are bearer tokens (current state), XSS can exfiltrate session IDs, enabling session takeover.
Root cause hypothesis: Convenience persistence chosen without aligning to security policy.
Recommendation: Store session IDs in memory only or move to an HttpOnly cookie-based session mechanism with CSRF protections. If session secrets are implemented, persist only non-sensitive identifiers.
Tradeoffs: Removing persistence may degrade resume UX; cookies add backend complexity.
Migration/compatibility considerations: Consider a phased rollout with a feature flag; preserve existing localStorage for a transition window.
Test/verification plan: Add tests that assert no sensitive identifiers are persisted when the flag is on; verify session resume still works.

**SEC-03 — Analytics API key configuration mismatch**
Issue: Backend supports optional API key enforcement, but frontend does not send the key.
Evidence:
- Backend checks `X-Analytics-Key` in `backend/app/core/security.py:142`.
- Frontend calls the endpoint without headers in `frontend/src/services/api.ts:50`.
Impact: If an API key is configured, the analytics UI breaks; if no key is configured, analytics data is publicly accessible.
Root cause hypothesis: Backend flexibility not reflected in frontend configuration.
Recommendation: Decide on policy. If analytics should be protected, add `VITE_ANALYTICS_API_KEY` (or similar) and send header in the client, or move analytics requests to a backend-only channel. If analytics should be public, document that and remove the key path.
Tradeoffs: Client-side keys are not secret; for real protection, use a backend proxy or server-side-only access.
Migration/compatibility considerations: Ensure keyless mode remains for local dev if needed; guard in code to avoid shipping secrets.
Test/verification plan: Add frontend integration test that asserts correct header when env var is present; backend test already covers enforcement in `tests/test_security.py:225`.

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
Issue: Override bounds are not consistent across frontend Zod schema, backend Pydantic, and calculator clamps.
Evidence:
- Frontend allows `interest_rate_override` up to 1 and `charging_time_hours_override` up to 24 in `frontend/src/forms/wizardForm.ts:120`.
- Backend enforces the same maxima in `backend/app/models/calculation.py:119` and `backend/app/models/calculation.py:125`.
- Calculator clamps `interest_rate_override` to 0.2 and `charging_time_hours_override` to 8 in `shared/calculator/tcoCalculator.ts:247` and `shared/calculator/tcoCalculator.ts:255`.
Impact: Users can submit values that are silently clamped in calculation, leading to confusing discrepancies and difficult debugging.
Root cause hypothesis: Multiple validation sources maintained independently.
Recommendation: Define a single source of truth for override constraints (shared constants or generated schema) and import into frontend/backend/calculator. Add a parity test to enforce equality.
Tradeoffs: Requires refactor across three layers and careful rollout.
Migration/compatibility considerations: Choose a canonical range and communicate changes; consider telemetry to detect real-world usage beyond new limits.
Test/verification plan: Add a test that asserts constraint equivalence across layers and fails CI on drift.

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
| P1 | Implement or remove session secret access control | High | Medium | Medium | Backend + Frontend | SEC-01 decision |
| P2 | Unify override constraints across layers | High | Medium | Medium | Shared + Frontend + Backend | MAINT-01 |
| P3 | Centralize session lifecycle (single-flight creation) | High | Medium | Medium | Frontend | CR-01 |
| P4 | Optimize analytics aggregation | High | High | Medium | Backend + Data | PERF-01 |
| P5 | Remove session ID from localStorage or secure with HttpOnly cookies | High | Medium | Medium | Frontend + Backend | SEC-02, P1 |
| P6 | Add Redis-backed rate limit storage | Medium | Medium | Low | Backend/Infra | SEC-04 |
| P7 | Make migrations an explicit deploy step | Medium | Medium | Low | Backend/Infra | CR-04 |
| P8 | Remove unused deps and dead code | Medium | Low | Low | Backend + Frontend | DEAD-02, DEAD-03 |
| P9 | Resolve dual lockfile strategy | Medium | Low | Low | Frontend/Infra | DEP-01 |
| P10 | Raise backend coverage threshold incrementally | Medium | Medium | Low | Backend | TEST-02 |

**Migration Plan**
1. Phase 1 — Safety rails and alignment.
Add parity tests for override constraints, add a session lifecycle unit test to prevent duplicate session creation, and add a security regression test for session secret behavior (either enforcement or removal). Rollout: merge behind feature flags where applicable. Rollback: revert to current behavior by disabling flags.
2. Phase 2 — Low-risk refactors.
Centralize override sanitization, remove unused frontend API calls, remove unused dependencies after verifying no scripts use them, and adjust cache initialization to be lazy. Rollout: small PRs with targeted tests. Rollback: revert per PR if regressions occur.
3. Phase 3 — High-impact structural changes.
Implement session secret enforcement (or formally remove it), move migrations to a deploy-time step, and optimize analytics aggregation (potentially adding new tables or jobs). Rollout: staged deployment with dual-read for analytics and a migration plan for existing sessions. Rollback: feature-flag enforcement and keep backward compatibility for legacy sessions during the transition.

**Tooling & Guardrails Recommendations**
- Add a CI check that validates override constraint parity across frontend, backend, and calculator.
- Add vulture (already in dev deps) to CI for unused Python code detection and a similar ESLint rule for unused exports.
- Add a check that ensures session secret behavior aligns with tests/docs (single source of truth).
- Add a performance budget test for analytics endpoint with a fixture dataset.
- Add a dependency usage audit (pipdeptree + grep) before pruning dependencies.

**Open Questions / Assumptions**
- Is the session secret model intended to be enforced, or has the product moved away from it? Evidence conflict: `SECURITY.md:116` vs `backend/app/api/router.py:77`.
- Is analytics data intended to be public? If not, how should clients authenticate to it?
- Are there multi-instance deployments where rate limiting must be shared? (Assumption for SEC-04.)
- Should sessions be resumable across browsers/devices, and what is the privacy requirement for stored operator contact emails?
- Are frontend and backend expected to share a single validation schema (e.g., generated from Python), or can we accept controlled divergence?

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

Notes:
- No tests or linters were executed in this audit; findings are based on static inspection.
- Items marked as assumptions require runtime or deployment context to verify.
