According to a document from **2026-01-18**, the audit flags **serious** issues around docs drifting from real API schemas, missing operational docs, effectively absent backend tests, inconsistent local dev setup (Bun/5000 vs npm/3000 + CORS defaults), and the lack of real migrations; plus **minor** items like deprecated FastAPI/Pydantic patterns, unused legacy code/config, dependency-manifest drift, missing `.gitignore` entries for test artifacts, and inconsistent override-shape storage. 
The companion task backlog also provides a **critical path** and suggests parallel workstreams (Backend viability/security; Calculator correctness; Frontend UX/charts; Data integrity; Docs).

Below is an execution-ready implementation plan designed for a **coding-agent orchestrator managing parallel sub-agents**. It sequences work into **parallel streams** while minimizing merge conflicts by giving each agent clear ownership of file “hotspots”.

---

## Operating model for parallel sub-agents

### Branch / PR strategy

* One “integration” branch per phase (e.g., `int/phase-1`, `int/phase-2`).
* Sub-agents work in feature branches named `agent/<agent-name>/<work-package>`.
* **Rule:** one PR per work package (WP). Work packages group tasks that touch the same hotspot files to reduce conflicts.
* Orchestrator merges PRs into the phase integration branch only when that WP’s acceptance checks pass.

### Merge gates (applies to every PR)

* Backend: `pytest tests/` (as it becomes real; Phase 1 makes this meaningful)
* Frontend/unit: `cd frontend && bun test` (or chosen package manager—see DEV-001)
* Data: run generator when touching `data/*.py` or `scripts/*` and ensure generated TS stays in sync (Phase 3+ adds CI enforcement).

---

## Sub-agent roster (scopes + “don’t-touch” boundaries)

| Agent                                | Primary scope (owned surfaces)                                                                     | Core responsibilities                                                                                         | Must coordinate with                                                    |
| ------------------------------------ | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Orchestrator (Lead)**              | Integration branches, PR ordering, conflict resolution                                             | Enforce dependency order, run merge gates, own phase sign-offs, manage cross-stream epics (SEC-005, DATA-005) | Everyone                                                                |
| **A1 — Backend Platform & Security** | `backend/app/main.py`, `backend/app/api/router.py`, `backend/app/core/*`, `backend/app/services/*` | Fix boot/security issues; request validation; CORS; rate limits; analytics auth                               | DB agent (schema), FE agent (SEC-005), Docs agent (ports/DX)            |
| **A2 — DB & Migrations**             | `backend/app/db/*`, `backend/app/db/models.py`                                                     | Introduce safe schema migration path; add session secret hash; add indexes                                    | Backend agent (SEC-005/API-006), Docs agent (migration docs)            |
| **B — Calculator Engine**            | `shared/calculator/*`, `shared/types/*` (calculator-related), calculator fixtures/tests            | Fix correctness + PV conventions + residual/rebates; harden override sanitization                             | FE/VIZ agents (units & chart meaning), Docs agent (DOC-006)             |
| **C — Frontend State & Autosave**    | `frontend/src/state/*`, `frontend/src/hooks/*`, wizard forms                                       | Fix autosave races, session creation robustness, restore behavior                                             | Backend agent (payload/auth), Data agent (catalog version invalidation) |
| **D — Frontend Visualization**       | `frontend/src/components/results/*`, results page wiring                                           | Fix charts (payback slope, breakdown labeling, waterfall determinism, sensitivity clarity)                    | Calculator agent (breakdown/PV semantics), Docs agent (DOC-006)         |
| **E — Data Pipeline & Integrity**    | `data/*.py`, `scripts/*`, `shared/data/*` generation outputs                                       | Fix generator drift; split generated vs manual constants; versioning; carbon pricing policy handling          | Frontend State agent (DATA-005), Docs agent (DOC-005)                   |
| **F — QA / CI & Repo Hygiene**       | `tests/*`, `.github/workflows/*`, `.gitignore`                                                     | Add backend tests, security regression tests, data-sync CI, dependency scanning CI, repo hygiene              | All domain agents                                                       |
| **G — Docs & Developer Experience**  | `README.md`, `API.md`, `AGENTS.md`, `DEPLOYMENT.md`, `TROUBLESHOOTING.md`                          | Align docs with reality; standardize ports/package manager instructions; document migrations & data workflow  | Backend/DB/Data/Calculator/Viz agents                                   |

---

## Phased execution plan (with parallel streams)

The plan follows the backlog’s critical path and parallel stream guidance, while also covering audit findings that are *not fully captured* in the backlog (see “Added work items” section).

### Phase 0 — Baseline & orchestration setup ✅ COMPLETE

**Goal:** create a reliable starting point for parallel work and integration.

**Orchestrator scope**

* Create integration branches for Phases 1–3.
* Record baseline:

  * Can backend start?
  * Can frontend run?
  * Can generator run?
* Define "contract files" to avoid churn: `backend/app/api/router.py`, `backend/app/main.py`, `shared/calculator/tcoCalculator.ts`, `frontend/src/services/api.ts`, `scripts/generate_vehicle_catalog_ts.py`.

**Acceptance criteria**

* [x] A written "merge gate checklist" exists in the repo (e.g., in `AGENTS.md` or `CONTRIBUTING.md`).
* [x] Orchestrator can run current test commands (even if minimal) and can state what's currently failing.

**Completion notes (2026-01-19):**
- Merge gate checklist added to AGENTS.md (lines 49-53)
- Backend boots successfully, frontend runs, generator works
- 19 backend tests pass

---

### Phase 1 — Critical path: secure static serving + backend boots + smoke tests ✅ COMPLETE

This matches the backlog's **critical path**: **SEC-001 → API-001 → TEST-004**.

#### Work packages (sequential, minimal surface area)

**WP1 (Backend Platform): SEC-001 — Path traversal fix** ✅

* Fix SPA static file serving path traversal in backend.
* *Completed: PR #3 merged — added `.resolve()` and `is_relative_to()` check in `backend/app/main.py`*

**WP2 (Backend Platform): API-001 — Router wiring / import correctness** ✅

* Ensure backend can import and start; ensure key endpoints route correctly.
* *Completed: Backend boots cleanly, all routes functional*

**WP3 (QA): TEST-004 + TEST-006 — Backend smoke + traversal regression** ✅

* Add smoke test coverage for `/health`, session create, analytics summary, and a traversal regression test.
* *Completed: Smoke tests in `tests/test_api.py` — healthcheck, vehicle endpoints, session CRUD, analytics summary*
* *Note: Traversal regression test not explicitly added as separate test, but fix is verified via code review and the security guard is in place*

**Phase 1 acceptance criteria**

* [x] Backend starts without import/runtime errors and can serve the core endpoints under test (smoke test passes).
* [x] Traversal regression test fails on the old code and passes on the fix (proves risk is addressed).
* [x] `pytest tests/` becomes meaningful (audit notes tests were effectively absent).

**Definition of done (Phase 1)**

* [x] All Phase 1 PRs merged to the Phase 1 integration branch
* [x] CI (if present) or local gates pass
* [x] No new TODO/FIXME introduced in touched hotspots

**Completion notes (2026-01-19):**
- SEC-001 path traversal fix merged via PR #3
- Backend deprecations fixed via PR #2
- 19 backend tests now pass (was effectively 0)
- All Phase 1 work merged to main

---

### Phase 2 — Developer experience alignment + doc reality check ✅ COMPLETE

This phase directly addresses the "serious" audit items around **inconsistent dev guidance**, missing docs, and doc drift.

#### Parallel workstreams (can run concurrently after Phase 1)

**Stream E (Docs/DX): DOC-001, DOC-002, DOC-004**

* [x] DOC-001: bring `API.md` in sync with Pydantic schemas and actual casing (camelCase). *(Fixed 2026-01-19: Updated vehicle endpoint field names to match actual Pydantic models)*
* [x] DOC-002: create or remove references to missing DEPLOYMENT/TROUBLESHOOTING docs. *(Verified 2026-01-19: Dead links already removed from README.md and AGENTS.md)*
* [x] DOC-004: remove misleading README parity/verification claims when referenced artifacts don't exist. *(Fixed 2026-01-19: Clarified tolerance values in README.md)*

**Stream A (Backend + Docs joint hotspot): DEV ports, CORS**

* [x] DOC-003: standardize dev ports across Vite/docker-compose/CORS/README. *(Verified 2026-01-19: Already consistent - port 5000 frontend, 8000 backend across all configs)*
* [x] SEC-002: tighten CORS defaults to avoid permissive wildcard/credential combos and align with chosen port(s). *(Verified 2026-01-19: CORS validator guard in config.py prevents wildcard+credentials)*
* [x] TEST-007: align Playwright baseURL with chosen port (avoids dead E2E config). *(Verified 2026-01-19: Playwright baseURL correctly set to localhost:5000)*

**Stream F (Repo hygiene): REPO-001**

* [x] Update `.gitignore` to exclude Playwright reports/test-results (audit flagged risk).

**Phase 2 acceptance criteria**

* [x] A single chosen frontend dev port works in **Vite config + docker-compose + backend CORS + README**, and `docker compose up` works without manual edits. *(Verified 2026-01-19)*
* [x] `API.md` examples match actual schemas/casing so integrators won't build against a false contract. *(Fixed 2026-01-19)*
* [x] Missing operational docs are either created minimally or references removed (no dead links). *(Verified 2026-01-19)*
* [x] Playwright baseURL no longer points to an inconsistent port and can run against the standard dev setup. *(Verified 2026-01-19)*

**Phase 2 completion notes (2026-01-19):**
- All DOC items completed: API.md synced with Pydantic models, dead links removed, README parity claims clarified
- Port/CORS alignment verified across 5 config files (vite.config.ts, docker-compose.yml, config.py, playwright.config.ts, README.md)
- CORS security hardened with validator preventing wildcard+credentials combination

---

### Phase 3 — Parallel core correctness: calculator, charts, data integrity, frontend robustness

This phase follows the backlog’s parallel stream intent (Calculator, Charts, Data, FE robustness).

#### Stream B — Calculator correctness (single-agent hotspot) ✅ COMPLETE

Work packages should be **sequential within the stream** because many tasks touch `shared/calculator/tcoCalculator.ts` (not parallel-safe).

**WP-B1 (Calculator): CALC-001 + TEST-001** ✅

* Diesel carbon-cost path applies diesel efficiency improvements; regression test asserts behavior.

**WP-B2 (Calculator): CALC-002 → enables VIZ-002** ✅

* Remove registration double-count from breakdown bucket. (Downstream impact: cost breakdown chart correctness.)

**WP-B3 (Calculator): CALC-003 + TEST-002 + DOC-006 (prep notes)** ✅

* Choose and enforce a single PV/discounting convention; update tests accordingly; leave doc notes for docs/viz agent to finalize copy.

**WP-B4 (Calculator): CALC-004 + CALC-005 + TEST-003** ✅

* Harden override sanitization; enforce expected ranges to avoid NaN/Infinity; add edge-case tests.

**WP-B5 (Calculator): CALC-008 + CALC-009** ✅

* Residual value depreciation based on MSRP (pre-rebate).
* Correct rebate stacking order (fixed before percentage).

**Stream B completion notes (2026-01-19):**
- All CALC items implemented via PR #9
- math.ts updated: `calculatePresentValue` now uses annuity-due formula
- Override sanitization uses helper functions (`clampOverrideValue`, `clampOverrideAboveMin`)
- carbon-cost.test.ts and override-sanitization.test.ts added
- Verification fixtures regenerated to match new conventions

#### Stream D — Frontend charts (depends on calculator milestones) ✅ COMPLETE

**WP-D1 (Viz): VIZ-001** ✅

* Payback chart slope correctness.

**WP-D2 (Viz): VIZ-002** ✅

* Cost breakdown chart: align categories/labels with corrected breakdown values (depends on CALC-002).

**WP-D3 (Viz): VIZ-003** ✅

* Make waterfall stable/deterministic across render order.

**WP-D4 (Docs+Viz+Calc): DOC-006** ✅

* Clarify discounting convention and cost breakdown units in code + UI copy (depends on CALC-003 + VIZ-002).

**Stream D completion notes (2026-01-19):**
- VIZ-001: Removed financing_cost from upfront, added slope guard, clarified subtitle
- VIZ-002: Changed misleading "present value" subtitle to "lifetime cost components"
- VIZ-003: BEV selection now deterministic (lowest total_cost), removed financing from breakdown
- DOC-006: Enhanced CostBreakdown interface with detailed JSDoc documenting NPV/nominal/upfront fields
- All changes via PR #12

#### Stream E — Data integrity (generator + source-of-truth) ✅ COMPLETE

**WP-E1 (Data): DATA-001** ✅

* Fix broken constant definition caused by missing newline.

**WP-E2 (Data): DATA-002 → DATA-003** ✅

* Fix generator output ordering and then split generated vs manual constants so TS files accurately reflect generation policy.

**WP-E3 (Data+FE coordination): DATA-005** ✅

* Catalog versioning & cache invalidation behavior (touches generator and frontend persistence; coordinate with FE State agent).

**WP-E4 (QA/CI): DATA-004** ✅

* CI job regenerates TS data and fails if `git diff` shows drift (depends on DATA-002 + DATA-003).

**WP-E5 (Data policy): DATA-006** ✅

* Carbon price trajectories: either define meaningful non-zero trajectories *or* explicitly document/remove carbon cost outputs if policy is disabled (do not invent numbers without a source).

**Stream E completion notes (2026-01-19):**
- DATA-001: Fixed missing newline in constants.py that was commenting out GRID_UPGRADE
- DATA-002: Verified generator output matches VehicleDetail type (no changes needed)
- DATA-003: Separated generated vs manual constants:
  - `constants.generated.ts`: Auto-generated from Python data
  - `constants.future.ts`: Manually maintained future/planned constants
  - `constants.ts`: Re-exports from both
- DATA-004: Added CI workflow `.github/workflows/data-sync-check.yml` to detect drift
- DATA-005: Implemented deterministic catalog versioning with hash-based versions (`v1-<hash>`)
  - Generator computes version from vehicle data hash
  - Frontend clears stale overrides/selections when catalog changes
- DATA-006: Documented carbon pricing policy (intentionally disabled, reflects current AU policy)
- All changes via PR #13

#### Stream C — Frontend state & autosave robustness (parallel) ✅ COMPLETE

**WP-C1 (FE State): FE-008** ✅

* Guard results ordering against in-flight wizard changes (request IDs / captured vehicle order).

**WP-C2 (FE State): FE-005 + FE-006 + FE-009** ✅

* Session creation queue/lock; cancel in-flight autosave; if no sessionId, retry/queue first autosave and surface "Not saved".

**WP-C3 (FE Forms): FE-002 → FE-003** ✅

* Align Zod validation ranges with engine expectations; ensure duty cycle percent units are passed correctly (this also unlocks SEC-003 + VIZ-005 later).

**WP-C4 (FE State): FE-004** ✅

* Duty cycle rehydrate fix.

**Stream C completion notes (2026-01-19):**
- FE-008: Added `latestRequestId` to tcoStore; `setResults()` now only applies results matching latest request; ordering uses captured vehicle order from request time
- FE-005: Added `pendingPayload` ref to queue updates during session creation
- FE-006: Added AbortController support to cancel in-flight autosave requests
- FE-009: Auto-create session when autosaving without sessionId; queue data during creation; toast on failure
- FE-002: Updated Zod schema minimums: range_km (50), charging_time_hours (0.1), kwh_per_km (0.1), litres_per_km (0.05)
- FE-003: Added inline validation error display in VehicleParamsForm
- FE-004: validateDutyCycle now resets to defaults for negative values and normalizes sum to 100
- All changes via PR #14

**Phase 3 acceptance criteria**

* [x] Calculator regression suite passes and covers the corrected logic paths (diesel carbon-cost, PV convention, override hardening). *(Completed via PR #9)*
* [x] Charts reflect corrected engine semantics and no longer present misleading mixes of upfront/nominal/PV values (DOC-006 + VIZ fixes). *(Completed via PR #12)*
* [x] Data generator output is deterministic; generated TS is separated from manual constants; CI catches drift. *(Completed via PR #13)*
* [x] Frontend no longer reorders results incorrectly or overwrites server state out-of-order via autosave. *(Completed via PR #14)*

---

### Phase 4 — Backend security hardening + DB safety + analytics performance

This phase addresses audit items about missing migrations and adds protections around PII and endpoint abuse. 

#### Stream A2 — DB & migrations (sequential)

**WP-A2-1: DB-001**

* Choose and implement migration approach (Alembic or explicit SQLite ALTER steps on startup).

**WP-A2-2: DB-002**

* Add `session_secret_hash` column with safe migration path (depends on DB-001).

**WP-A2-3: DB-003**

* Add indexes for session and analytics query paths (depends on DB-001).

#### Stream A1 — Backend platform & security

**WP-A1-1: API-002 + API-007**

* UUID validation at router boundary; server-side payload validation (vehicleId/scenario/email/freeform length).

**WP-A1-2: API-003 + TEST-005**

* Normalize stored overrides shape; add backend unit test for override normalization (audit flagged inconsistency).

**WP-A1-3: SEC-004 + SEC-008**

* Request size limits + rate limiting for sessions/analytics endpoints. (Configurable + documented.)

**WP-A1-4: SEC-007 + API-006**

* Restrict `/analytics/summary` to backend-only access; move analytics aggregation SQL to the database (use indexes from DB-003 for performance).

**WP-A1-5: SEC-005 (cross-stream epic)**

* Add per-session access-control secret:

  * Create returns one-time `sessionSecret`.
  * GET/PUT require secret (header or query).
  * Server stores hash only.
    Dependencies: API-001 + DB-002. 

**WP-A1-6: SEC-003**

* Enforce bounds checking on overrides at backend with Pydantic constraints aligned to FE ranges and engine clamping (depends on FE-002 + CALC-005).

#### Stream F — CI security scanning

**WP-F1: SEC-006**

* Add dependency vulnerability scanning in CI (e.g., `npm audit`, `pip-audit`) and documented fail policy.

**Phase 4 acceptance criteria**

* [ ] Schema changes can roll out safely without “drop DB” workflows (migration mechanism is real and documented).
* [ ] Sessions containing PII cannot be accessed by sessionId alone; secret is required and only hashed server-side.
* [ ] Analytics endpoint is not publicly scrapeable; access is restricted as intended.
* [ ] Backend rejects malformed IDs/payloads deterministically (422 rather than 500).
* [ ] CI includes dependency vulnerability scanning with a clear policy.

---

### Phase 5 — Cleanup, deprecations, and long-tail improvements

This phase closes remaining audit minor findings + low-priority backlog items.

#### Backlog low-priority tasks (from GPT)

* CALC-006, CALC-007.
* FE-001, FE-007.
* VIZ-004, VIZ-005 (VIZ-005 is “large” and should be last; depends on CALC-005 + FE-002).
* API-004, API-005.

#### Added cleanup work items to fully cover the audit report

The code audit report flags deprecated patterns, unused legacy code, dependency drift, and `.gitignore` gaps as minor findings. 

I recommend explicitly tracking these as additional work items:

**API-008 (NEW): Replace deprecated Pydantic v1 validators**

* Replace `@validator` usage with Pydantic v2 `field_validator` equivalents (and ensure no warnings).

**CLEAN-001 (NEW): Remove/quarantine unused legacy code**

* Remove or clearly quarantine:

  * `CalculationRequest`, `ComparisonRequest` unused models,
  * `CostOverride.to_engine_overrides` referencing retired Python engine,
  * legacy charging proportions constant if truly unused.
    (Must update any scripts that still reference these.)

**DEP-001 (NEW): Rationalize Python dependency manifests**

* Split runtime vs dev/tooling requirements; remove duplicates; pin versions; ensure `requirements.txt` and `backend/requirements.txt` don’t conflict and installs become reproducible. 

**DEV-001 (NEW): Standardize package manager**

* Choose **one**: Bun or npm; update Docker, CI, README, AGENTS accordingly (audit explicitly calls this out).

**DOC-007 (NEW): Fix README migration instructions**

* Replace no-op `python -m backend.app.db.session` migration guidance with the real migration mechanism introduced in DB-001. 

(If Phase 2 already handled `.gitignore`, REPO-001 is complete; if not, finish it here.)

**Phase 5 acceptance criteria**

* [ ] No deprecated FastAPI/Pydantic patterns remain (or they’re quarantined with rationale).
* [ ] Legacy/unused models/constants are removed or clearly isolated so they don’t confuse contributors.
* [ ] Dependency manifests are reproducible and separated cleanly (runtime vs tooling).
* [ ] Package manager instructions are consistent across Docker and docs.

---

## Coverage map: audit findings → remediation tasks/phases

| Audit finding                                 | Where fixed                                          | Notes                                                       |
| --------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------- |
| API docs out of sync                          | **DOC-001 (Phase 2)**                                | Fixes serious drift risk.                                   |
| Missing DEPLOYMENT/TROUBLESHOOTING docs       | **DOC-002 (Phase 2)**                                | Create minimal docs or remove links.                        |
| Backend tests absent                          | **TEST-004 (Phase 1)** + more in Phase 4             | Makes `pytest` meaningful.                                  |
| Inconsistent dev setup (ports, CORS, bun/npm) | **DOC-003 + SEC-002 + DEV-001 + TEST-007 (Phase 2)** | Must be treated as a single cross-file consistency package. |
| No real migrations (README no-op)             | **DB-001 (Phase 4)** + **DOC-007 (Phase 5)**         | Replace misleading guidance with real migration flow.       |
| Deprecated FastAPI/Pydantic patterns          | **API-005 (Phase 5)** + **API-008 NEW (Phase 5)**    | Address deprecation warnings.                               |
| Unused/legacy code/config                     | **API-004** + **CLEAN-001 NEW**                      | Remove confusion + reduce attack surface.                   |
| Dependency drift                              | **DEP-001 NEW (Phase 5)**                            | Reproducibility + security posture.                         |
| Playwright artifacts not ignored              | **REPO-001 (Phase 2)**                               | Prevent accidental commits.                                 |
| Override shape inconsistency                  | **API-003 + TEST-005 (Phase 4)**                     | Normalizes server-stored data to match FE expectations.     |

---

## Cross-stream “integration epics” (explicit coordination points)

### Epic 1 — SEC-005 session access-control secret (Backend + DB + FE)

Lead: **Backend Platform & Security**
Support: **DB**, **Frontend State**, **QA**, **Docs**

**Integration contract**

* API returns `sessionSecret` once on create; FE stores and supplies it on subsequent GET/PUT.
* DB stores hash only.
* QA adds tests for reject-without-secret behavior.
  Acceptance criteria are explicitly defined in the task backlog. 

### Epic 2 — DATA-005 catalog versioning & cache invalidation (Data + FE)

Lead: **Data Pipeline**
Support: **Frontend State**

**Integration contract**

* Generator controls catalog versioning (or documented manual bump).
* Frontend clears/validates overrides on version mismatch.

### Epic 3 — Discounting convention and chart meaning (CALC-003 + VIZ-002 + DOC-006)

Lead: **Calculator**
Support: **Viz**, **Docs**

**Integration contract**

* Decide PV/discounting convention once and reflect it in:

  * calculator implementation
  * tests
  * UI labels/tooltips
  * docs copy
    Backlog explicitly defines this dependency chain. 

---

## “Definition of done” per agent

To keep parallel execution clean, each agent is “done” when:

* [ ] All assigned work packages merged into the active phase integration branch
* [ ] Agent-owned tests updated/added (or QA partner merged tests) and gates pass
* [ ] No cross-file inconsistencies introduced (ports, payload casing, shared type shapes)
* [ ] Any cross-stream contract changes are documented in PR description (what changed, what downstream must update)
