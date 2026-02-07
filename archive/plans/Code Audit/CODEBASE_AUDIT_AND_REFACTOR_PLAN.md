**Current Priorities (Remaining)**
None. All items in this plan are implemented as of 2026-02-05.

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
- CI lint/test coverage is defined in `.github/workflows/ci.yml` with a backend coverage floor at 60%. Evidence: `.github/workflows/ci.yml:68`.
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
None. The previously listed risks are resolved by the changes recorded below.

**Remaining Findings**
None. All items from this audit plan have been implemented and moved to the Completed Work section.

**Open Questions / Assumptions**
- Session secrets are now enforced for new sessions; should we backfill/rotate secrets for legacy sessions (null `session_secret_hash`) and enforce universally?
- Should session secret cookies use a different TTL or rotation strategy for long-lived resumes?

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
- PERF-01: Analytics aggregation now uses SQL joins/aggregates instead of loading all rows in memory.
- SEC-02: Session secrets now persist via HttpOnly cookies; frontend stops persisting secrets in localStorage; cookie refresh on read/update; tests updated.
- SEC-04: slowapi rate limiting now uses Redis-backed storage (configurable) with coverage.
- MAINT-02/AI-03: Duty-cycle validation comments now match behavior; tests assert non-100 sums are preserved without warnings.
- MAINT-03: Added shared `sanitizeWizardData` and reuse across autosave/session payload building with unit coverage.
- DEAD-02: Removed unused frontend vehicle API calls.
- DEAD-03: Removed unused Python deps (`orjson`, `marshmallow`, `cerberus`, `loguru`).
- DEP-01: Kept `bun.lock` as source of truth and removed committed `package-lock.json` (CI still generates it for npm audit).
- TEST-02: Raised backend coverage floor to 60%.
- OPS-01: Guarded Uvicorn `--reload` in compose via `UVICORN_RELOAD`.

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

**SEC-02 — Session secret stored in localStorage**
Status (2026-02-05): Resolved. Secrets are now stored in HttpOnly cookies and no longer persisted to localStorage; update/get refresh cookie for migration.

**SEC-03 — Analytics access now server-side only**
Status (2026-02-05): Implemented. Analytics UI removed; analytics endpoint now requires `ANALYTICS_API_KEY` and is disabled if unset.

**SEC-04 — Rate limiting likely per-process only (assumption)**
Status (2026-02-05): Resolved. slowapi is configured with Redis-backed storage via settings; test verifies configured storage.

**Performance**

**PERF-01 — Analytics aggregation loads all calculation rows into memory**
Status (2026-02-05): Resolved. Analytics aggregation now uses SQL joins and aggregates to avoid loading full result tables into memory.

**Maintainability**

**MAINT-01 — Validation ranges drift across layers**
Status (2026-02-05): Resolved by centralizing limits in `data/constants.py` (`OVERRIDE_LIMITS`) and consuming them in frontend/backend; shared constants regenerated.

**MAINT-02 — Comment/code mismatch in duty-cycle validation**
Status (2026-02-05): Resolved. Comment updated to match behavior (no sum validation), and tests assert non-100 sums are preserved without warnings.

**MAINT-03 — Duplicate payload sanitization logic**
Status (2026-02-05): Resolved. Added shared `sanitizeWizardData` in `frontend/src/utils/payload.ts`, reused in autosave and session payload builder; unit test added.

**Duplication & Dead Code**

**DEAD-01 — Session secret helpers and DB column now used**
Status (2026-02-05): Resolved; helpers and `session_secret_hash` are now used for session access control.

**DEAD-02 — Unused frontend API calls**
Status (2026-02-05): Resolved. Removed `fetchVehicles` and `fetchVehicle` from `frontend/src/services/api.ts`.

**DEAD-03 — Unused Python dependencies**
Status (2026-02-05): Resolved. Removed unused runtime deps (`orjson`, `marshmallow`, `cerberus`, `loguru`) from `requirements.txt`.

**Dependency Health**

**DEP-01 — Dual lockfiles and audit generation may drift**
Status (2026-02-05): Resolved via Option A. `bun.lock` remains the source of truth; committed `frontend/package-lock.json` removed and ignored while CI generates one for npm audit.

**Tests & Observability**

**TEST-01 — Session secret tests now align with API**
Status (2026-02-05): Resolved; API returns `sessionSecret` on create and enforces `X-Session-Secret` on GET/PUT, and tests validate this.

**TEST-02 — Backend coverage floor is low**
Status (2026-02-05): Resolved. Coverage gate raised to 60% in `.github/workflows/ci.yml`.

**Build/Deploy Ergonomics**

**OPS-01 — `docker-compose` runs backend with `--reload`**
Status (2026-02-05): Resolved. Compose now gates reload via `UVICORN_RELOAD` (default `1` for dev).

**AI-Generated Pattern Indicators (Resolved)**

**AI-01 — Over-defensive validation scattered across layers**
Status (2026-02-05): Resolved by centralizing override limits with shared `OVERRIDE_LIMITS`.

**AI-02 — Error swallowing without observability**
Status (2026-02-05): Resolved for cache + secret verification via narrower exception handling and logging.

**AI-03 — Comment drift from behavior**
Status (2026-02-05): Resolved. Duty-cycle validation comment updated; tests lock intended behavior.

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
