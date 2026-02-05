**Current Priorities (Remaining)**
| ID | Title | Impact | Effort | Risk | Owner Suggestion | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Optimize analytics aggregation | High | High | Medium | Backend + Data | PERF-01 |
| P2 | Review session secret storage (localStorage vs HttpOnly) | High | Medium | Medium | Frontend + Backend | SEC-02 |
| P3 | Add Redis-backed rate limit storage | Medium | Medium | Low | Backend/Infra | SEC-04 |
| P4 | Remove unused deps and dead code | Medium | Low | Low | Backend + Frontend | DEAD-02, DEAD-03 |
| P5 | Resolve dual lockfile strategy | Medium | Low | Low | Frontend/Infra | DEP-01 |
| P6 | Raise backend coverage threshold incrementally | Medium | Medium | Low | Backend | TEST-02 |
| P7 | Guard `--reload` in production compose | Medium | Low | Low | Backend/Infra | OPS-01 |
| P8 | Fix duty-cycle comment drift | Low | Low | Low | Frontend | MAINT-02 |
| P9 | Deduplicate payload sanitization | Low | Low | Low | Frontend | MAINT-03 |

**Still-Relevant Context**
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

**Top Remaining Risks & Hotspots**
| Rank | Risk | Likelihood | Impact | Score | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Session secret stored in localStorage (XSS exposure risk) | 3 | 4 | 12 | `frontend/src/state/tcoStore.ts`, `frontend/src/services/api.ts` |
| 2 | Analytics aggregation loads full table in memory | 3 | 4 | 12 | `backend/app/services/sessions.py:210`, `backend/app/services/sessions.py:220` |
| 3 | Rate limiting likely per-process only (slowapi default storage) | 3 | 3 | 9 | `backend/app/core/security.py:85` |
| 4 | Dual lockfile strategy can drift | 2 | 3 | 6 | `frontend/bun.lock`, `frontend/package-lock.json`, `.github/workflows/dependency-audit.yml:90` |
| 5 | Unused deps and dead code increase surface area | 3 | 2 | 6 | `requirements.txt:20`, `frontend/src/services/api.ts:17` |
| 6 | Backend coverage floor is low | 2 | 3 | 6 | `.github/workflows/ci.yml:68` |
| 7 | Compose runs backend with `--reload` | 2 | 2 | 4 | `docker-compose.yml:7` |
| 8 | Comment drift from behavior (duty cycle validation) | 2 | 2 | 4 | `frontend/src/state/tcoStore.ts:241` |

**Remaining Findings**
**Security & Privacy**

**SEC-02 — Session secret stored in localStorage**
Issue: Session secret is persisted to localStorage for resume; if XSS occurs it can be exfiltrated and used to access sessions.
Status (2026-02-05): Implemented for resume UX alongside secret enforcement.
Evidence:
- Store persistence includes `sessionSecret` in `frontend/src/state/tcoStore.ts`.
- Session API client sends `X-Session-Secret` in `frontend/src/services/api.ts`.
Follow-up: Consider HttpOnly cookies, tighter CSP, shorter secret TTLs, or avoiding persistence when possible.

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

**Open Questions / Assumptions**
- Session secrets are now enforced for new sessions; should we backfill/rotate secrets for legacy sessions (null `session_secret_hash`) and enforce universally?
- Analytics access is server-side only (API key required); do we want an internal/admin UI or a separate reporting workflow to view analytics?
- Are there multi-instance deployments where rate limiting must be shared? (Assumption for SEC-04.)
- Should sessions be resumable across browsers/devices, and do we want to move session secret storage to HttpOnly cookies or shorten secret TTLs?

**Completed Work (Implemented)**
**Progress Update (2026-02-05)**
Completed:
- Session secret enforcement implemented end-to-end: create returns `sessionSecret`, backend stores a bcrypt hash and requires `X-Session-Secret` for session GET/PUT; frontend persists/sends the secret; tests updated.
- Override validation ranges unified to the calculator via shared `OVERRIDE_LIMITS` in `data/constants.py`; frontend and backend now consume the same limits; shared constants regenerated.
- Analytics UI removed from frontend (unused components/hooks deleted and API client call removed).
- Analytics endpoint now requires `ANALYTICS_API_KEY`; if unset, endpoint is disabled (403). Tests and docs updated accordingly.
- CR-01: Centralized frontend session lifecycle with a shared single-flight create path and queued updates; autosave and calculation hooks now route through a common service.
- CR-02/CR-03: Session cache is cache-first with cached secret hash; Redis client is lazily initialized with retry/backoff and resets on failure.
- CR-04: Runtime migrations are gated by `RUN_MIGRATIONS` (defaults to enabled in development, disabled otherwise); startup skips migrations when disabled.
- CR-05: Secret verification now logs expected errors and returns HTTP 500 on unexpected failures; added test coverage.

**Correctness & Reliability**

**CR-01 — Duplicate session creation paths can race**
Status (2026-02-05): Implemented. Added a shared session lifecycle service with a single-flight create path and queued updates; autosave and calculations now route through it, plus a single-flight unit test.

**CR-02 — Cache doesn’t avoid the first DB hit**
Status (2026-02-05): Implemented. Session lookup now checks Redis first using cached payload + secret hash and falls back to DB on cache miss or legacy entry; added cache-hit coverage.

**CR-03 — Redis client initialization is one-shot**
Status (2026-02-05): Implemented. Redis client is lazily initialized with retry/backoff and resets to allow reconnection after failures; retry coverage added.

**CR-04 — Migrations run on app startup**
Status (2026-02-05): Implemented. Added `RUN_MIGRATIONS` gate and a test ensuring startup skips migrations when disabled.

**CR-05 — Broad exception swallowing in secret verification**
Status (2026-02-05): Implemented. `verify_secret` now logs expected errors and surfaces unexpected failures as HTTP 500; test coverage added.

**Security & Privacy**

**SEC-01 — Session access-control secret enforced**
Status (2026-02-05): Implemented end-to-end. Session creation generates a secret, stores a bcrypt hash, and requires `X-Session-Secret` for GET/PUT. Frontend persists and sends the secret; tests updated.

**SEC-03 — Analytics access now server-side only**
Status (2026-02-05): Implemented. Analytics UI removed; analytics endpoint now requires `ANALYTICS_API_KEY` and is disabled if unset.

**Maintainability**

**MAINT-01 — Validation ranges drift across layers**
Status (2026-02-05): Resolved by centralizing limits in `data/constants.py` (`OVERRIDE_LIMITS`) and consuming them in frontend/backend; shared constants regenerated.

**Duplication & Dead Code**

**DEAD-01 — Session secret helpers and DB column now used**
Status (2026-02-05): Resolved; helpers and `session_secret_hash` are now used for session access control.

**Tests & Observability**

**TEST-01 — Session secret tests now align with API**
Status (2026-02-05): Resolved; API returns `sessionSecret` on create and enforces `X-Session-Secret` on GET/PUT, and tests validate this.

**AI-Generated Pattern Indicators (Resolved)**

**AI-01 — Over-defensive validation scattered across layers**
Status (2026-02-05): Resolved by centralizing override limits with shared `OVERRIDE_LIMITS`.

**AI-02 — Error swallowing without observability**
Status (2026-02-05): Resolved for cache + secret verification via narrower exception handling and logging.

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
