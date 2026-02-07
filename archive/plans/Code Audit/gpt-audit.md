**Codebase Audit And Refactor Plan**
**Executive Summary**
The most urgent reliability risk is the request-size middleware: for chunked requests it marks `size_exceeded` and returns a 413 only after the handler has already run, which can allow side effects before rejection; it also relies on a private `_receive` hook that could break on framework upgrades. Evidence: `backend/app/core/middleware.py:24`, `backend/app/core/middleware.py:66`, `backend/app/core/middleware.py:68`, `backend/app/core/middleware.py:72`.
Session access control is also exposed more broadly than necessary: the session secret is returned in the JSON response and stored in JS memory while also being set as an HttpOnly cookie, increasing the XSS blast radius. Evidence: `backend/app/models/session.py:219`, `backend/app/api/router.py:112`, `frontend/src/services/sessionLifecycle.ts:94`, `frontend/src/services/api.ts:20`.
Validation limits are duplicated and hard-coded in the shared calculator rather than read from the canonical limits in `data/constants.py`, creating drift risk between frontend, backend, and shared logic. Evidence: `data/constants.py:85`, `frontend/src/forms/wizardForm.ts:62`, `shared/calculator/tcoCalculator.ts:138`.
Analytics aggregation scales with the number of BEV models because it runs one query per BEV–diesel pair; this is fine at 8 BEVs but will degrade as the catalog grows. Evidence: `backend/app/services/sessions.py:225`, `backend/app/services/sessions.py:244`, `backend/app/services/sessions.py:274`.
There are also small but meaningful cleanup opportunities (unused API helpers and unused exception branches) that add noise and are consistent with AI-assisted guard patterns. Evidence: `frontend/src/services/api.ts:49`, `backend/app/api/router.py:112`, `backend/app/services/sessions.py:46`.

**Repo Overview**
Constraints snapshot (observed in repo docs):
Target runtime/platform(s): Python 3.11+, Node.js 20+, Bun 1.0+, PostgreSQL 15+, Redis 7+ from `README.md:28`.
Languages/frameworks: FastAPI/SQLAlchemy/Pydantic for backend, React/TypeScript/Vite for frontend, shared TypeScript calculator from `README.md:127`, `README.md:140`, `frontend/package.json:6`.
Deployment environment(s): Docker Compose with backend, frontend, Postgres, Redis services in `docker-compose.yml:3`.
Performance/SLO constraints: Not specified in repo.
Security/compliance constraints: Not specified in repo.
Backward compatibility requirements: Not specified in repo.
“Do not touch” areas: `archive/` is explicitly called out as historical in `README.md:121` (treat as read-only unless asked).
Preferred coding standards/linting rules: Python black/isort/ruff in `pyproject.toml:1`, frontend ESLint/Prettier in `frontend/package.json:10`.

Architecture map and key entry points:
Backend API entrypoint is `backend/app/main.py:31`, which wires middleware, CORS, and routes from `backend/app/api/router.py:34`.
Backend persistence uses SQLAlchemy models in `backend/app/db/models.py:11` and session management in `backend/app/services/sessions.py:43`.
Frontend entrypoint is `frontend/src/main.tsx:1`, with state in `frontend/src/state/tcoStore.ts:24` and calculation triggers in `frontend/src/hooks/useCalculations.ts:31`.
Shared calculator lives in `shared/calculator/tcoCalculator.ts:1` with math utilities in `shared/calculator/math.ts:1` and types in `shared/types/tco.types.ts:1`.
Data generation flows from Python data to TS via `scripts/generate_vehicle_catalog_ts.py:1` producing `shared/data/*` artifacts.
Integration points: frontend calls backend via axios with `/api/v1` base and credentials in `frontend/src/services/api.ts:9`, backend mounts routes and serves SPA assets in `backend/app/main.py:59`.

**Top Risks & Hotspots**
1. Request-size middleware can allow handler side effects on oversized bodies before returning 413. Likelihood: Medium. Impact: High. Evidence: `backend/app/core/middleware.py:24`, `backend/app/core/middleware.py:68`, `backend/app/core/middleware.py:72`.
2. Session secret is returned to JS and stored client-side while also set as HttpOnly cookie. Likelihood: Medium. Impact: High. Evidence: `backend/app/models/session.py:219`, `backend/app/api/router.py:112`, `frontend/src/services/sessionLifecycle.ts:94`.
3. bcrypt hashing/verification is called directly in async handlers, risking event-loop blocking under load. Likelihood: Medium. Impact: Medium. Evidence: `backend/app/core/security.py:123`, `backend/app/services/sessions.py:46`.
4. Validation limits are duplicated and hard-coded across layers, risking drift. Likelihood: Medium. Impact: Medium. Evidence: `data/constants.py:85`, `frontend/src/forms/wizardForm.ts:62`, `shared/calculator/tcoCalculator.ts:138`.
5. Analytics summary uses one query per BEV–diesel pair, which scales linearly with catalog size. Likelihood: Low-Medium. Impact: Medium. Evidence: `backend/app/services/sessions.py:244`.
6. Scenario identifiers are inconsistent between request keys and stored calculation results. Likelihood: Medium. Impact: Low-Medium. Evidence: `shared/types/tco.types.ts:74`, `shared/calculator/tcoCalculator.ts:899`, `backend/app/services/sessions.py:395`.
7. Docker Compose runs dev servers with reload for backend and frontend, which is fragile if used beyond local dev. Likelihood: Low. Impact: Medium. Evidence: `docker-compose.yml:8`, `docker-compose.yml:34`.
8. No dependency update automation found; pinned dependencies may age without alerting. Likelihood: Medium. Impact: Medium. Evidence: `requirements.txt:9`, `frontend/package.json:14`.
9. Missing explicit tests for request size limit behavior. Likelihood: Medium. Impact: Medium. Evidence: `backend/app/core/middleware.py:15` (no test references found; see Appendix).
10. Dead/unused code paths and defensive catches add noise (e.g., unused `fetchSession`, unused ValueError handling). Likelihood: High. Impact: Low. Evidence: `frontend/src/services/api.ts:49`, `backend/app/api/router.py:112`.

**Findings**
**Correctness & Reliability**
**CR-1 Request Size Limit Can Allow Side Effects**
Issue: Oversized bodies are detected during streaming but the middleware still calls `call_next` before returning 413, so handlers can run on partial/truncated bodies and commit side effects. Evidence: `backend/app/core/middleware.py:49`, `backend/app/core/middleware.py:68`, `backend/app/core/middleware.py:72`.
Impact: Risk of partial writes or inconsistent state on large/chunked requests; potential for unexpected behavior under malicious or malformed payloads.
Root cause hypothesis: The middleware relies on a post-processing check and private `request._receive` override rather than aborting processing mid-stream. Evidence: `backend/app/core/middleware.py:66`.
Recommendation: Abort request execution immediately when size is exceeded by raising an HTTPException inside `limited_receive` or by short-circuiting before `call_next` once `size_exceeded` is set. Consider using Starlette’s `RequestValidationError` or a custom exception to terminate downstream processing.
Tradeoffs: Early abort may surface different error types to clients (e.g., 413 instead of 422) and will need careful handling for streaming clients.
Migration/compatibility considerations: Ensure clients tolerate 413 for oversized bodies; document max size in API docs.
Test/verification plan: Add tests that send chunked bodies larger than `max_request_body_size` and assert no DB writes occur (e.g., create session with oversized payload), plus assert 413 response.

**CR-2 Scenario Identifier Drift in Stored Results**
Issue: Calculation responses return `scenario_name` as scenario display name, while request payloads and other parts of the system use scenario keys. Evidence: `shared/types/tco.types.ts:74`, `shared/calculator/tcoCalculator.ts:899`, `backend/app/services/sessions.py:395`.
Impact: Stored results contain mixed identifiers, complicating analytics filters, data exports, or migrations that assume a scenario key.
Root cause hypothesis: Calculator uses `scenario.name` for presentation while downstream persistence stores that value verbatim.
Recommendation: Store both `scenario_key` and `scenario_label`, or change calculator to return the key and derive label in the UI. Update DB schema or payload accordingly.
Tradeoffs: Changing schema requires migration and backfill; keeping both increases payload size but improves clarity.
Migration/compatibility considerations: If changing stored values, backfill existing rows or version the API to avoid breaking analytics consumers.
Test/verification plan: Add a regression test verifying scenario identifiers in stored `CalculationResultRecord` rows match expected keys.

**CR-3 File Handle Leak in Offline Migration Generator**
Issue: `run_migrations_offline` opens a file handle without closing it. Evidence: `backend/app/db/session.py:81`, `backend/app/db/session.py:92`.
Impact: Minor resource leak in CLI usage; can matter in long-lived tooling or repeated invocations.
Root cause hypothesis: Convenience code path omits context manager.
Recommendation: Wrap output file handling with `with open(...) as f:` and set `config.output_buffer = f`.
Tradeoffs: Minimal; behavior remains the same.
Migration/compatibility considerations: None.
Test/verification plan: Unit test that calls `run_migrations_offline` with a temp file and ensures the file handle is closed (or use context manager).

**Security & Privacy**
**SEC-1 Session Secret Exposed to JS**
Issue: Session secrets are returned in the JSON response and stored client-side while also set as HttpOnly cookies. Evidence: `backend/app/models/session.py:219`, `backend/app/api/router.py:112`, `frontend/src/services/sessionLifecycle.ts:94`, `frontend/src/services/api.ts:20`.
Impact: Increases the blast radius of XSS since JS can read the session secret; undermines the protections of HttpOnly cookies.
Root cause hypothesis: Session lifecycle was designed to work with header-based auth before cookie-only flow was added.
Recommendation: Make the HttpOnly cookie the single source of truth and stop returning `sessionSecret` in JSON for browser clients. For non-browser clients, provide a separate token flow or an opt-in API flag.
Tradeoffs: Cookie-only flow may complicate cross-origin API clients and needs CSRF considerations (SameSite policy, CSRF tokens).
Migration/compatibility considerations: Introduce a transition period where both cookie and header are accepted, then deprecate JSON secret.
Test/verification plan: Add integration tests verifying session updates succeed with cookie-only flow and fail without cookie when `sessionSecret` is omitted.

**SEC-2 bcrypt on the Event Loop**
Issue: bcrypt hash and verify are synchronous and executed inside async request flows. Evidence: `backend/app/core/security.py:123`, `backend/app/core/security.py:136`, `backend/app/services/sessions.py:46`, `backend/app/services/sessions.py:98`.
Impact: CPU-bound hashing can block the event loop under load, causing latency spikes or DoS amplification.
Root cause hypothesis: Security helpers are synchronous and used directly in async handlers.
Recommendation: Offload bcrypt operations to a worker thread (e.g., `anyio.to_thread.run_sync`) or use a dedicated async-friendly password hashing utility.
Tradeoffs: Slight complexity in async/await boundaries; may reduce throughput if thread pool is under-provisioned.
Migration/compatibility considerations: Ensure thread pool size is configured; keep hashing parameters consistent.
Test/verification plan: Add load tests (or unit tests with timing assertions) to confirm request latency does not spike with repeated session operations.

**Performance**
**PERF-1 Analytics Aggregation Performs N Queries**
Issue: `_compute_outcomes_optimized` runs one query per BEV–diesel pair. Evidence: `backend/app/services/sessions.py:244`, `backend/app/services/sessions.py:257`, `backend/app/services/sessions.py:274`.
Impact: Query count scales linearly with the number of BEV models; this will increase load as catalog grows.
Root cause hypothesis: The method prioritizes simple per-pair aggregation over a single grouped query.
Recommendation: Replace per-pair loop with a single query that joins BEV and diesel rows and aggregates by pair in one pass, or precompute analytics in a materialized table.
Tradeoffs: More complex SQL and potentially larger in-memory post-processing; but better scaling.
Migration/compatibility considerations: None if the output shape remains the same.
Test/verification plan: Add a benchmark test or query count assertion in analytics tests.

**PERF-2 Payload Deduplication Uses Custom Stable Stringify**
Issue: `stableStringify` sorts and serializes the full payload for every calculation run, which can be costly for large payloads. Evidence: `frontend/src/hooks/useCalculations.ts:13`.
Impact: Mild CPU overhead on frequent recalculation cycles; may show up on low-power devices.
Root cause hypothesis: Custom deduplication avoids re-running computations but is implemented via full serialization.
Recommendation: Replace with a stable hash of only the fields that influence calculation, or use a memoized comparison function.
Tradeoffs: Reduced generality; requires care to include all relevant fields.
Migration/compatibility considerations: Ensure hash includes any newly introduced fields.
Test/verification plan: Add tests verifying identical inputs skip recomputation and different inputs do not.

**Maintainability**
**MAINT-1 Hard-Coded Override Limits in Calculator**
Issue: The calculator sanitizes overrides using hard-coded numeric ranges instead of reading `OVERRIDE_LIMITS`. Evidence: `shared/calculator/tcoCalculator.ts:138`, `data/constants.py:85`, `frontend/src/forms/wizardForm.ts:62`.
Impact: Drift risk when limits change; potential inconsistent validation across frontend, backend, and calculator.
Root cause hypothesis: Sanitization logic was duplicated for runtime safety rather than centralized.
Recommendation: Generate and import override limits into the calculator from `shared/data/constants.generated.ts` and use those values for sanitization.
Tradeoffs: Requires tight coupling between generator and calculator; but improves consistency.
Migration/compatibility considerations: Regenerate shared data after updating constants; ensure tests are updated if limits change.
Test/verification plan: Add tests asserting calculator clamps according to `OVERRIDE_LIMITS`.

**MAINT-2 Divergent Duty-Cycle Validation Across Layers**
Issue: The store resets invalid duty-cycle values, the calculator normalizes to 100%, and the backend rejects sums outside tolerance. Evidence: `frontend/src/state/tcoStore.ts:94`, `shared/calculator/tcoCalculator.ts:126`, `backend/app/models/session.py:100`.
Impact: Inconsistent behavior between UI, calculator, and API; difficult to reason about error states and persisted data.
Root cause hypothesis: Each layer implemented its own guardrails for user safety without shared validation rules.
Recommendation: Define a shared duty-cycle validation policy and enforce it consistently, ideally by exporting a shared validator or schema.
Tradeoffs: Less flexibility for each layer to “helpfully” repair invalid data.
Migration/compatibility considerations: Communicate UX changes (e.g., no silent resets) to stakeholders.
Test/verification plan: Add tests that verify identical duty-cycle inputs are handled consistently across store, calculator, and backend.

**Duplication & Dead Code**
**DUP-1 Unused API Helper**
Issue: `fetchSession` is defined but not referenced elsewhere. Evidence: `frontend/src/services/api.ts:49` and no references found via repo search (see Appendix).
Impact: Unused code increases maintenance surface and can rot.
Root cause hypothesis: Feature was planned but not used after moving to session persistence updates.
Recommendation: Remove `fetchSession` or add usage where needed (e.g., resume flow).
Tradeoffs: If later needed, you’ll reintroduce it; removal reduces clutter.
Migration/compatibility considerations: Ensure no external consumers depend on it.
Test/verification plan: None if removed; add tests if resume flow is implemented.

**DUP-2 Unused ValueError Handling in Router**
Issue: Router catches `ValueError` from session creation even though the service does not raise it. Evidence: `backend/app/api/router.py:112`, `backend/app/services/sessions.py:46`.
Impact: Noise and false sense of error handling coverage.
Root cause hypothesis: Defensive coding template carried forward.
Recommendation: Remove unused `ValueError` branches or document which code path could raise it.
Tradeoffs: If future code adds `ValueError`, this handler might be useful; otherwise it’s dead weight.
Migration/compatibility considerations: None.
Test/verification plan: Ensure API still returns 422 for validation errors via Pydantic.

**Dependency Health**
**DEP-1 No Automated Dependency Update Workflow**
Issue: Dependencies are pinned (Python) or caret-ranged (frontend) without an update automation config. Evidence: `requirements.txt:9`, `frontend/package.json:14` and no dependabot/renovate config found (see Appendix).
Impact: Security patches may be missed and upgrades become batchy and risky.
Root cause hypothesis: Dependency hygiene is manual today.
Recommendation: Add Dependabot or Renovate configuration to keep runtime and dev dependencies current with controlled cadence.
Tradeoffs: Increased PR noise; requires triage discipline.
Migration/compatibility considerations: Start with monthly updates and widen once stable.
Test/verification plan: Ensure CI runs on dependency-update PRs.

**Tests & Observability**
**TEST-1 Missing Explicit Tests for Request Size Limits**
Issue: No tests were found targeting the request-size middleware behavior. Evidence: `backend/app/core/middleware.py:15` and repo search results (see Appendix).
Impact: Regressions in request-size handling can slip into production.
Root cause hypothesis: Middleware added without test harness.
Recommendation: Add tests that validate 413 responses for oversized payloads and assert no DB writes.
Tradeoffs: Adds test setup complexity for large payloads.
Migration/compatibility considerations: None.
Test/verification plan: Add unit tests using `httpx.AsyncClient` with large payloads.

**OBS-1 Limited Observability Instrumentation**
Issue: No explicit tracing/metrics instrumentation (OpenTelemetry, Prometheus, Sentry) was found in the backend or frontend code. Evidence: repo search results (see Appendix).
Impact: Harder to diagnose performance regressions or failures in production.
Root cause hypothesis: Observability was not prioritized during initial implementation.
Recommendation: Add structured logging and optional tracing (e.g., OpenTelemetry) to key request paths and calculator performance.
Tradeoffs: Additional runtime overhead and config complexity.
Migration/compatibility considerations: Start with logging and request metrics; add tracing later.
Test/verification plan: Add smoke tests verifying instrumentation hooks run without errors.

**Build/Deploy Ergonomics**
**BUILD-1 Docker Compose Uses Dev Servers**
Issue: Compose uses `uvicorn --reload` and `bun run dev` directly, which is intended for dev and not production. Evidence: `docker-compose.yml:8`, `docker-compose.yml:34`.
Impact: Risk of accidental deployment of dev servers with hot reload, low performance, and weaker security defaults.
Root cause hypothesis: Single compose file serving both dev and potential prod usage.
Recommendation: Split into `docker-compose.dev.yml` and `docker-compose.prod.yml` (or document clearly), using production-grade commands for prod.
Tradeoffs: Additional maintenance of multiple compose files.
Migration/compatibility considerations: Update README to clarify intended usage.
Test/verification plan: Verify production compose can build and run the app with expected ports.

**AI-Generated Patterns**
**AI-1 Overly Defensive Sanitization and Guard Clauses**
Issue: Multiple layers sanitize or reset data with guard clauses that can hide root causes (e.g., duty-cycle resets and override clamping). Evidence: `shared/calculator/tcoCalculator.ts:126`, `frontend/src/state/tcoStore.ts:94`, `frontend/src/forms/wizardForm.ts:30`.
Why it’s risky: Silent correction makes debugging difficult and can mask upstream data issues.
How to refactor: Replace ad-hoc guard clauses with a shared schema-driven validator; make corrections explicit and surfaced to the UI.
How to test: Add tests that assert invalid inputs are rejected with clear errors rather than silently normalized.

**AI-2 Error Swallowing with Console Warns**
Issue: Persist flows catch and log errors without a structured recovery path. Evidence: `frontend/src/hooks/useCalculations.ts:47`, `frontend/src/services/sessionLifecycle.ts:46`.
Why it’s risky: Errors can be silently ignored, leaving the UI in an inconsistent state (e.g., user believes state was saved when it wasn’t).
How to refactor: Surface errors to a user-visible notification and retry strategy; capture errors in a centralized error boundary.
How to test: Add tests that simulate failed persistence and verify UI error surfaces and retry behavior.

**Prioritized Backlog**
| ID | Title | Impact | Effort | Risk | Owner Suggestion | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Abort oversized requests before handler runs | High | Medium | Medium | Backend | TEST-1 |
| B2 | Move session secret to cookie-only flow | High | Medium | Medium-High | Backend + Frontend | B1 |
| B3 | Offload bcrypt to thread pool | Medium | Medium | Medium | Backend | B2 |
| B4 | Align scenario identifiers (key vs label) | Medium | Medium | Low-Medium | Shared + Backend | B5 |
| B5 | Centralize override limits in calculator | Medium | Medium | Low | Shared | - |
| B6 | Collapse analytics aggregation into single query | Medium | Medium-High | Medium | Backend | - |
| B7 | Remove dead code and unused exception paths | Low | Low | Low | Frontend + Backend | - |
| B8 | Add middleware and persistence tests | Medium | Low | Low | Backend + Frontend | B1 |
| B9 | Add dependency update automation | Medium | Low | Low | DevOps | - |
| B10 | Split dev/prod compose configs | Low | Low | Low | DevOps | - |

**Migration Plan**
Phase 1: Safety Rails
Add tests for oversized request handling and session persistence failure paths before refactoring. Add CI steps for pytest/vitest/lint to prevent regressions. Rollout: keep current behavior, only add tests and CI. Rollback: revert CI changes if needed.

Phase 2: Low-Risk Refactors
Remove unused code paths, centralize override limits in the calculator, and standardize duty-cycle validation behavior across layers. Rollout: feature-flag any user-facing validation changes if UX impact is expected. Rollback: retain previous validation in a fallback path for one release.

Phase 3: High-Impact Changes
Move session authentication to cookie-only flow, offload bcrypt to worker threads, and optimize analytics queries. Rollout: use “branch by abstraction” by supporting both header- and cookie-based auth for a transition period; introduce a feature flag to switch analytics query paths. Rollback: revert to header-based auth and previous analytics query logic.

**Tooling & Guardrails Recommendations**
Add CI gates for `python -m pytest tests --cov`, `ruff`, `black`, and `mypy` using repo configs in `pyproject.toml:1`.
Add frontend CI gates for `bun run lint`, `bun run typecheck`, and `bun run test` per `frontend/package.json:7`.
Add security checks `pip-audit` and `bandit` (already in `requirements-dev.txt`) and gate on clean results.
Add a data consistency gate to run `python scripts/generate_vehicle_catalog_ts.py` and `python scripts/validation.py` when `data/*.py` changes.
Add dependency update automation (Dependabot/Renovate) to keep both `requirements.txt` and `frontend/package.json` fresh.

**Open Questions / Assumptions**
Assumption: There is no hidden dependency update automation; no dependabot/renovate config was found via search. Confirm if update tooling exists elsewhere.
Assumption: Request size limit should reject oversized payloads before any business logic executes; confirm if partial processing is acceptable.
Assumption: Session secrets can move to cookie-only flow; confirm non-browser clients and any integration requirements.
Open question: Are there performance targets for analytics endpoints beyond current scale?

**Appendix**
Commands run (representative): `ls`, `cat README.md`, `cat docker-compose.yml`, `cat requirements.txt`, `cat frontend/package.json`, `sed -n` and `nl -ba` on key files, `rg -n` for symbol/reference searches.
Notes: No tests, linters, or static analysis were executed during this audit.
Additional references: `README.md` for architecture and commands, `docker-compose.yml` for service topology, `scripts/generate_vehicle_catalog_ts.py` for data generation.
