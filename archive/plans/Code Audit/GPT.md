## Executive Summary

**Overall health score: 6/10 (mixed).** The core TypeScript calculator is fairly readable and has a meaningful frontend test suite, but there are several **material correctness and consistency issues** (diesel carbon-cost path ignores efficiency improvements, inconsistent PV discounting conventions across categories, and a double-count in the cost breakdown). On the frontend, a few results charts (notably payback and cost breakdown) present values in ways that can be misleading because they mix *upfront*, *nominal lifetime totals*, and *present values* while labelling outputs as “present value” drivers.

The **highest risk areas** are on the backend and security side: the API router currently references **non-existent services/modules** (will fail to import/start as-is), and the SPA file-serving route is vulnerable to **path traversal** (arbitrary file reads) if the frontend `dist/` directory exists. Data integrity is also at risk because the TS data files are described as auto-generated, but the generator scripts and the committed outputs appear **out of sync**, increasing the chance of silent drift between Python “authoritative” data and frontend/shared usage.

Remediation effort is **moderate overall**: most critical items are small-to-medium fixes (router wiring, traversal fix, PV consistency, breakdown bug, and a few UI chart corrections). A smaller number of items are “large” (session access control tokenization, proper sensitivity analysis via recomputation, and hardening the data generation workflow with CI enforcement).

---

## Task Backlog

### Domain: Calculator Engine

(Tasks related to `shared/calculator/*`, `shared/types/*`)

#### CALC-001: Apply diesel efficiency improvements to diesel carbon cost

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L302-321`
* **Problem:** `calculateCarbonCostYear()` for diesel uses `vehicle.litres_per_km` directly and **does not apply** `scenario.diesel_efficiency_improvement`, unlike the diesel fuel-cost path which does apply an efficiency multiplier.
* **Impact:** Diesel carbon costs are overstated in scenarios where diesel efficiency improves, distorting `carbon_cost` and `total_cost`, and weakening scenario credibility.
* **Acceptance Criteria:**

  * [ ] Diesel carbon litres/km is scaled by `getSeriesValue(scenario.diesel_efficiency_improvement, year, 1)` (or equivalent) before multiplying by annual kms.
  * [ ] For a scenario where diesel efficiency improves (<1), diesel `carbon_cost` is lower than baseline given identical inputs.
* **Dependencies:** None
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Small (< 1 hour)

---

#### CALC-002: Remove registration double-count from `taxes_and_fees` breakdown bucket

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L717-723`
* **Problem:** `taxesAndFees` is computed as `stampDuty + annual_registration * VEHICLE_LIFE` while `registration_cost` is also separately reported as `annual_registration * VEHICLE_LIFE`. This **double counts registration** in breakdown consumers.
* **Impact:** Charts/insights that use `breakdown.*` can materially misrepresent cost drivers and savings attribution.
* **Acceptance Criteria:**

  * [ ] `taxes_and_fees` excludes registration (i.e., becomes stamp-duty-only) **or** `registration_cost` is removed and all callers updated (choose one).
  * [ ] No other breakdown buckets overlap (at minimum: registration not present in two buckets).
* **Dependencies:** None
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Small (< 1 hour)

---

#### CALC-003: Align PV treatment of insurance/registration with the engine’s discount convention

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/math.ts:L14-28`, `shared/calculator/tcoCalculator.ts:L644-651`
* **Problem:** Most annual series PVs use `discountToPresent(year)` with `year=1 → discount exponent 0` (`math.ts:L15-16`), but insurance/registration PV uses `calculatePresentValue()` (`math.ts:L18-28`), which is the **ordinary annuity** formula (first payment end of year 1). This is an internal inconsistency.
* **Impact:** Total PV costs are inconsistent by category; small individually but credibility-impacting in an audit context.
* **Acceptance Criteria:**

  * [ ] Insurance and registration PV are computed using the same convention as other annual cashflows (either update `calculatePresentValue` to annuity-due or stop using it and use `calculateNpvOfAnnualCashflows` with constant arrays).
  * [ ] In-code comments accurately describe the convention used.
* **Dependencies:** None
* **Parallel Safe:** No (touches shared math + calculator)
* **Estimated Scope:** Medium (1-4 hours)

---

#### CALC-004: Harden calculator inputs against invalid per-vehicle overrides that can create NaN/Infinity

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L78-204`, `shared/calculator/tcoCalculator.ts:L206-241`, `shared/calculator/tcoCalculator.ts:L336-378`
* **Problem:** `sanitizePayload()` only filters numeric overrides by `>= 0`, allowing values like `range_km_override = 0`, which can lead to **division by zero** in `calculateChargingLabourCost()` (`usableRange` used as divisor).
* **Impact:** Can crash calculations, create NaN/Infinity outputs, or silently corrupt results.
* **Acceptance Criteria:**

  * [ ] `sanitizePayload()` rejects or clamps overrides that are used as divisors (minimums enforced at least for `range_km_override`, `charging_time_hours_override`, and energy intensity overrides).
  * [ ] `calculateChargingLabourCost()` defensively handles `usableRange <= 0` (return 0 or throw a clear error) even if upstream validation fails.
* **Dependencies:** FE-002 (recommended alignment), but not required
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Medium (1-4 hours)

---

#### CALC-005: Enforce expected ranges for cost override multipliers in the engine

* **Priority:** Medium
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L137-176`, `shared/calculator/tcoCalculator.ts:L465-469`
* **Problem:** Engine accepts cost overrides with only `>= 0` validation. Out-of-range values can produce unrealistic or even negative effects (e.g., battery replacement adjustment uses `BATTERY_LIFE_VARIATION_BASE - override`).
* **Impact:** Non-UI clients (API callers, corrupted persisted state) can generate implausible outputs that look legitimate.
* **Acceptance Criteria:**

  * [ ] `sanitizePayload()` clamps or discards overrides outside UI-defined ranges (e.g., `battery_life_variation [0.5,1.5]`, `charging_efficiency_variation [0.7,1.3]`, etc.).
  * [ ] Battery replacement adjustment cannot produce negative cost multipliers.
* **Dependencies:** None
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Small (< 1 hour)

---

#### CALC-006: Remove unused `calculateBatteryHealth` dead code

* **Priority:** Low
* **Type:** Refactor
* **Files:** `shared/calculator/tcoCalculator.ts:L423-438`
* **Problem:** `calculateBatteryHealth()` is defined but never used.
* **Impact:** Increases cognitive load and suggests unimplemented battery degradation logic.
* **Acceptance Criteria:**

  * [ ] Function removed (or integrated into actual replacement logic with explicit use).
  * [ ] No unused-symbol lint warnings remain (if linting enabled).
* **Dependencies:** None
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Small (< 1 hour)

---

#### CALC-007: Make `getVehicleCatalogSnapshot()` name/shape match intent

* **Priority:** Low
* **Type:** Refactor
* **Files:** `shared/calculator/tcoCalculator.ts:L748-750`, `shared/calculator/index.ts:L1-3`, `shared/data/vehicleCatalog.ts:L6-13`
* **Problem:** `getVehicleCatalogSnapshot()` returns `VEHICLE_DETAILS` only, without the catalog version (`VEHICLE_CATALOG_VERSION` exists separately).
* **Impact:** Consumers can’t reliably validate cache/version compatibility using the “snapshot”.
* **Acceptance Criteria:**

  * [ ] Snapshot return includes both `version` and `vehicles` **or** function is renamed to reflect returning just the vehicles list.
* **Dependencies:** None
* **Parallel Safe:** No (touches shared calculator exports)
* **Estimated Scope:** Small (< 1 hour)

---

#### CALC-008: Base residual value depreciation on MSRP (pre-rebate)

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L540-612`
* **Problem:** `calculateResidualValueAtLife()` takes `initialCost` (which includes stamp duty and subtracts rebates) as the depreciation base, but the required convention is to depreciate off MSRP.
* **Impact:** Residual value and depreciation are understated for BEVs with large rebates, skewing total cost and payback.
* **Acceptance Criteria:**

  * [ ] Depreciation base uses `vehicle.msrp` (or an explicit MSRP-derived base), not `initialCost`.
  * [ ] Rebates and stamp duty do not reduce the residual value basis.
  * [ ] Verification fixtures/tests are updated to reflect the new residual values.
* **Dependencies:** None
* **Parallel Safe:** No (touches `shared/calculator/tcoCalculator.ts`)
* **Estimated Scope:** Medium (1-4 hours)

---

#### CALC-009: Apply rebate stacking order (fixed before percentage)

* **Priority:** High
* **Type:** Bug
* **Files:** `shared/calculator/tcoCalculator.ts:L523-537`, `data/policies.py:L105-150`
* **Problem:** `calculateBevPurchaseRebate()` applies the percentage rebate to full MSRP and then adds fixed rebates, but policy requires fixed incentives to apply first and the percentage to apply to the remaining MSRP.
* **Impact:** Total rebates are overstated vs intended policy when both fixed and percentage rebates are enabled, inflating BEV savings.
* **Acceptance Criteria:**

  * [ ] Percentage rebate is calculated on `max(0, msrp - fixedRebateApplied)` (fixed first).
  * [ ] Percentage rebate still respects `max_amount` on its own component.
  * [ ] Code comments or policy docs explicitly describe the stacking order.
* **Dependencies:** None
* **Parallel Safe:** No (touches calculator + policy conventions)
* **Estimated Scope:** Small (< 1 hour)

---

### Domain: Frontend State & Forms

(Tasks related to `frontend/src/state/*`, `frontend/src/components/wizard/*`, `frontend/src/forms/*`)

#### FE-001: Fix WizardPage duty-cycle fallback to match store defaults

* **Priority:** Low
* **Type:** Bug
* **Files:** `frontend/src/pages/WizardPage.tsx:L98-107`
* **Problem:** The watch fallback defaults duty cycle to `{ urban: 40, regional: 35, longHaul: 25 }`, which diverges from the store’s initial default `{60,25,15}` (`frontend/src/state/tcoStore.ts:L22-28`).
* **Impact:** In rare reset/rehydrate edge cases, users can get unexpected default duty cycles that shift results.
* **Acceptance Criteria:**

  * [ ] WizardPage fallback uses the same default as the store (`60/25/15`) or imports a shared constant.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### FE-002: Align Zod validation for per-vehicle overrides with UI constraints and engine assumptions

* **Priority:** High
* **Type:** Bug
* **Files:** `frontend/src/forms/wizardForm.ts:L120-130`, `frontend/src/components/wizard/VehicleParamsForm.tsx:L175-184`, `frontend/src/components/wizard/VehicleParamsForm.tsx:L220-306`
* **Problem:** Schema allows `range_km_override` min 0 and max 2000, while UI uses min 50 and max 2500; similarly `kwh_per_km_override`, `litres_per_km_override`, and `charging_time_hours_override` allow 0, which can produce invalid calculations.
* **Impact:** Invalid values can be saved (especially via manual entry/localStorage rehydrate), causing calculation instability or silent distortion.
* **Acceptance Criteria:**

  * [ ] `vehicleParamOverridesSchema` minimums/maximums match the UI component constraints.
  * [ ] Inputs that would cause division-by-zero are rejected at schema level (e.g., range and charging time must be > 0).
* **Dependencies:** CALC-004 (recommended), but not required
* **Parallel Safe:** No (touches shared validation rules used widely)
* **Estimated Scope:** Small (< 1 hour)

---

#### FE-003: Surface validation errors for per-vehicle override inputs (currently silent)

* **Priority:** Medium
* **Type:** UX/UI
* **Files:** `frontend/src/components/wizard/VehicleParamsForm.tsx:L56-83`, `frontend/src/components/wizard/VehicleParamsForm.tsx:L175-184`
* **Problem:** `safeParse()` failures in `handleOverrideChange()` simply return, with no user feedback. Users can enter values that appear accepted but are ignored.
* **Impact:** Confusing UX and undermines trust (“I changed the value but nothing happened”).
* **Acceptance Criteria:**

  * [ ] Invalid override input shows a clear inline error message (per-field).
  * [ ] The field either reverts or remains editable while displaying the error (but does not silently drop updates).
* **Dependencies:** FE-002
* **Parallel Safe:** No (touches same form as FE-002)
* **Estimated Scope:** Medium (1-4 hours)

---

#### FE-004: Make duty-cycle rehydration robust (sum and sign validation)

* **Priority:** Medium
* **Type:** Bug
* **Files:** `frontend/src/state/tcoStore.ts:L48-71`, `frontend/src/state/tcoStore.ts:L148-166`
* **Problem:** `onRehydrateStorage` only checks `NaN`, not negative values or totals ≠ 100. `validateDutyCycle()` clamps negatives but doesn’t enforce totals.
* **Impact:** Persisted invalid state can slip through and lead to backend validation errors or inconsistent internal weighting.
* **Acceptance Criteria:**

  * [ ] On rehydrate, duty cycle is normalized (or reset) if any value is invalid or if the sum is not ~100.
  * [ ] Store always maintains a dutyCycle that passes the Zod duty-cycle schema constraint.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### FE-005: Queue `persistSession()` when a session is being created to avoid dropped saves

* **Priority:** Medium
* **Type:** Bug
* **Files:** `frontend/src/hooks/useCalculations.ts:L68-112`
* **Problem:** If `persistSession()` is called while `isCreatingSession` is true, it returns early and the update is **dropped**.
* **Impact:** Users can complete a calculation and still lose results in the persisted session (especially with fast repeated calculate clicks or slow networks).
* **Acceptance Criteria:**

  * [ ] If called while creating, the latest payload is queued and sent immediately after create completes.
  * [ ] No calculation result is silently skipped due to create-in-flight.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### FE-006: Prevent autosave out-of-order updates (cancel in-flight autosave requests)

* **Priority:** Medium
* **Type:** Bug
* **Files:** `frontend/src/hooks/useWizardAutosave.ts:L31-82`, `frontend/src/services/api.ts:L70-92`
* **Problem:** Autosave can send multiple updates; older requests can finish after newer ones, overwriting newer wizard state on the server.
* **Impact:** Server session state can regress, leading to confusing restore behavior.
* **Acceptance Criteria:**

  * [ ] Autosave cancels any in-flight request when a newer autosave is scheduled (AbortController / axios cancel).
  * [ ] Only the latest wizard snapshot can reach the server.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### FE-007: Remove unused preview runner hook usage in WizardCompareStep

* **Priority:** Low
* **Type:** Refactor
* **Files:** `frontend/src/components/wizard/WizardCompareStep.tsx:L18-22`
* **Problem:** `useCalculationRunner()` is imported and destructured, but `runPreviewComparison` is unused.
* **Impact:** Dead code / lint noise; increases confusion about intended preview workflow.
* **Acceptance Criteria:**

  * [ ] Unused hook usage removed **or** component uses `runPreviewComparison` consistently for preview calculations.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### FE-008: Guard results ordering against in-flight wizard changes

* **Priority:** High
* **Type:** Bug
* **Files:** `frontend/src/state/tcoStore.ts:L104-116`, `frontend/src/hooks/useCalculations.ts:L33-96`
* **Problem:** `setResults()` orders incoming results using the *current* `wizardData` vehicle order, so async responses can be re-ordered to the wrong vehicle list if the user changes selection mid-flight.
* **Impact:** Results can be momentarily mislabeled or mapped to the wrong vehicle, causing incorrect comparisons.
* **Acceptance Criteria:**

  * [ ] Each calculation request carries a request ID or captured vehicle order, and results are only applied if they match the latest request.
  * [ ] Ordering is derived from the payload that produced the results, not mutable store state.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### FE-009: Autosave should retry or surface failure when no sessionId exists

* **Priority:** Medium
* **Type:** Bug
* **Files:** `frontend/src/hooks/useWizardAutosave.ts:L28-53`, `frontend/src/hooks/useCalculations.ts:L41-85`
* **Problem:** `useWizardAutosave()` returns early when `sessionId` is missing, and there is no retry or user-visible state when session creation fails.
* **Impact:** Users can progress through the wizard without any persisted state and without feedback until results are lost.
* **Acceptance Criteria:**

  * [ ] If `sessionId` is missing but wizard data exists, create a draft session (wizardData only) or queue the first autosave until session creation succeeds.
  * [ ] Surface a clear "Not saved" indicator or toast when session creation fails, and retry on next change.
* **Dependencies:** FE-005 (session creation flow), API-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

### Domain: Frontend Visualization

(Tasks related to `frontend/src/components/results/*`)

#### VIZ-001: Fix PaybackChart to avoid treating “financing_cost” as upfront and guard slope edge cases

* **Priority:** High
* **Type:** Bug
* **Files:** `frontend/src/components/results/PaybackChart.tsx:L31-37`, `frontend/src/components/results/PaybackChart.tsx:L62-81`
* **Problem:** Payback chart sets upfront = `purchase_cost + financing_cost`, but `financing_cost` is total nominal interest (not upfront). It also interpolates payback year using slope difference without guarding `dieselSlope === bevSlope`.
* **Impact:** Payback curves and payback-year can be materially incorrect or produce NaN/Infinity.
* **Acceptance Criteria:**

  * [ ] Upfront cost excludes `financing_cost` (or is replaced with a clearly-named “upfront payment” concept).
  * [ ] Payback-year interpolation handles equal slopes safely (returns null/undefined or “No payback within 15 years”).
  * [ ] Chart labels/tooltips clarify what the lines represent (e.g., “cumulative equivalent annual cost” if using `annual_cost` as slope).
* **Dependencies:** CALC-002 (recommended to avoid breakdown overlap), DOC-006 (label alignment)
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### VIZ-002: Correct CostBreakdownChart labelling and prevent misleading “present value cost drivers”

* **Priority:** High
* **Type:** Bug
* **Files:** `frontend/src/components/results/CostBreakdownChart.tsx:L32-35`, `frontend/src/components/results/CostBreakdownChart.tsx:L38-76`, `shared/types/tco.types.ts:L82-105`
* **Problem:** Chart subtitle claims “present value cost drivers” while the breakdown is explicitly mixed (PV + nominal lifetime totals + partial upfront), and currently includes overlapping buckets (`taxes_and_fees` vs `registration_cost`).
* **Impact:** High risk of misleading stakeholders about what’s driving cost differences.
* **Acceptance Criteria:**

  * [ ] Subtitle and tooltip explicitly state the unit basis used (PV vs nominal vs upfront), **or** chart is updated to use a PV-only, non-overlapping breakdown.
  * [ ] After CALC-002, registration is not shown twice.
* **Dependencies:** CALC-002
* **Parallel Safe:** No (depends on calculator breakdown change)
* **Estimated Scope:** Small (< 1 hour)

---

#### VIZ-003: Make SavingsWaterfallChart comparator selection deterministic and remove mixed-unit “financing savings”

* **Priority:** High
* **Type:** Bug
* **Files:** `frontend/src/components/results/SavingsWaterfallChart.tsx:L21-30`, `frontend/src/components/results/SavingsWaterfallChart.tsx:L36-94`
* **Problem:** Waterfall compares first diesel vs first BEV in `results`, and includes `financing_cost` and other mixed-unit fields in category savings attribution.
* **Impact:** Savings decomposition can be wrong vehicle-to-vehicle and misleading by unit.
* **Acceptance Criteria:**

  * [ ] Comparator pair is deterministic (e.g., baseline `results[0]` vs best BEV by `total_cost`, or user-selected BEV).
  * [ ] Waterfall categories use consistent units (PV vs nominal) and do not include `financing_cost` unless its unit basis is clearly stated and consistent.
* **Dependencies:** CALC-002, DOC-006
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### VIZ-004: Relabel SensitivityTornadoChart as “approximate” or recompute sensitivity properly

* **Priority:** Medium
* **Type:** Documentation
* **Files:** `frontend/src/components/results/SensitivityTornadoChart.tsx:L20-27`, `frontend/src/components/results/SensitivityTornadoChart.tsx:L33-90`
* **Problem:** Chart scales baseline category totals by ±20% instead of recomputing the model, which is not a true sensitivity analysis and can be inconsistent with nonlinearities (battery replacement, financing, PV discounting).
* **Impact:** Risk of stakeholders over-trusting “sensitivity” claims.
* **Acceptance Criteria:**

  * [ ] UI clearly labels this as a linearized/approximate sensitivity.
  * [ ] Tooltip explains it does not rerun the model (unless VIZ-005 is implemented).
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### VIZ-005: Implement true sensitivity analysis by rerunning calculator with parameter perturbations

* **Priority:** Low
* **Type:** Refactor
* **Files:** `frontend/src/components/results/SensitivityTornadoChart.tsx:L33-152`, `shared/calculator/tcoCalculator.ts:L243-297`
* **Problem:** Current sensitivity is not model-based.
* **Impact:** Limits analytical credibility; true recomputation would enable defensible insights.
* **Acceptance Criteria:**

  * [ ] For each factor (diesel, electricity, maintenance, residual, battery), recompute BEV and diesel `total_cost` with +20% and -20% override adjustments using `calculateComparison` (or equivalent).
  * [ ] Chart displays delta in `total_cost` (PV) rather than scaled category totals.
  * [ ] Results are cached/memoized to avoid expensive rerenders.
* **Dependencies:** CALC-005 (override range enforcement), FE-002 (UI ranges)
* **Parallel Safe:** No (touches shared assumptions and UI)
* **Estimated Scope:** Large (4+ hours)

---

### Domain: Backend API

(Tasks related to `backend/app/api/*`, `backend/app/services/*`)

#### API-001: Fix API router imports and service wiring so backend can start

* **Priority:** Critical
* **Type:** Bug
* **Files:** `backend/app/api/router.py:L1-26`, `backend/app/api/router.py:L30-89`, `backend/app/services/vehicles.py:L1-34`, `backend/app/services/sessions.py:L1-95`, `backend/app/models/session.py:L111-170`
* **Problem:** Router imports and instantiates non-existent `VehicleCatalogService` and `AnalyticsService`, and imports `AnalyticsSummary` from a missing module (`app.models.analytics`) even though `AnalyticsSummary` exists in `session.py`.
* **Impact:** Backend will fail to import and cannot run; analytics endpoint and vehicle endpoints are broken.
* **Acceptance Criteria:**

  * [ ] `/api/v1/vehicles` uses `VehicleService` (from `backend/app/services/vehicles.py`) and returns `VehicleSummary` list.
  * [ ] `/api/v1/analytics/summary` calls `SessionService.analytics_summary()` and returns `AnalyticsSummary` from `backend/app/models/session.py`.
  * [ ] Module imports succeed and a minimal app startup works.
* **Dependencies:** None
* **Parallel Safe:** No (single file hotspot)
* **Estimated Scope:** Medium (1-4 hours)

---

#### API-002: Validate `session_id` path params as UUIDs at the router boundary

* **Priority:** High
* **Type:** Bug
* **Files:** `backend/app/api/router.py:L38-54`, `backend/app/api/router.py:L62-79`
* **Problem:** `session_id` is treated as a plain string and passed into DB/cache. Invalid IDs should be rejected early.
* **Impact:** Reduces error handling ambiguity and prevents odd cache keys / log noise.
* **Acceptance Criteria:**

  * [ ] Router path params type `session_id` as `UUID` (or explicitly validate and return 422).
  * [ ] Invalid UUID returns 422 (or equivalent), not a 500.
* **Dependencies:** API-001
* **Parallel Safe:** No (touches same router file)
* **Estimated Scope:** Small (< 1 hour)

---

#### API-003: Normalize stored overrides shape in sessions to avoid schema drift

* **Priority:** High
* **Type:** Bug
* **Files:** `backend/app/services/sessions.py:L299-319`, `backend/app/services/sessions.py:L321-350`
* **Problem:** `_replace_inputs()` merges `vehicle_overrides` under `{ vehicle: ... }` but then writes it to `wizard_state["vehicleParamOverrides"]` (flattened), creating a shape mismatch between stored wizard state and expected frontend shape.
* **Impact:** Session restore can break or silently drop overrides; data integrity issues over time.
* **Acceptance Criteria:**

  * [ ] Stored `wizard_state` preserves the same structure as the frontend expects (keyed by vehicleId with override fields, not nested under `vehicle` unless frontend uses that).
  * [ ] Update path does not overwrite existing overrides with a different structure.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### API-004: Wire `Settings.cache_results` to actually control Redis caching behavior

* **Priority:** Medium
* **Type:** Refactor
* **Files:** `backend/app/core/config.py:L22-27`, `backend/app/services/sessions.py:L200-260`
* **Problem:** `cache_results` exists in settings but is unused; code always attempts Redis cache operations.
* **Impact:** Confusing configuration; unnecessary log noise and inconsistent behavior across environments.
* **Acceptance Criteria:**

  * [ ] When `cache_results` is false, the service does not attempt Redis reads/writes.
  * [ ] When true, Redis caching behaves as today.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### API-005: Replace deprecated FastAPI `on_event` hooks with lifespan context

* **Priority:** Low
* **Type:** Refactor
* **Files:** `backend/app/main.py:L51-66`
* **Problem:** Uses `@app.on_event("startup"/"shutdown")` which is deprecated in newer FastAPI versions.
* **Impact:** Future upgrade friction and deprecation warnings.
* **Acceptance Criteria:**

  * [ ] Startup/shutdown behavior implemented using FastAPI lifespan.
  * [ ] DB init and Redis close still occur as intended.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### API-006: Move analytics aggregation into SQL to avoid full-table scans

* **Priority:** High
* **Type:** Performance
* **Files:** `backend/app/services/sessions.py:L164-216`
* **Problem:** `_compute_outcomes()` loads every `calculation_results` row (including `result_payload`) into memory and aggregates in Python.
* **Impact:** Memory and latency grow linearly with dataset size; analytics can OOM the API service.
* **Acceptance Criteria:**

  * [ ] Use SQL aggregation (CTEs / subqueries) to compute win rate and average cost delta without loading all rows into Python.
  * [ ] Payback computation avoids loading full `result_payload` for all rows (use JSON operators in Postgres or compute on a reduced subset).
  * [ ] Endpoint remains accurate for BEV↔diesel pairs per session.
* **Dependencies:** DB-003 (indexes)
* **Parallel Safe:** Yes
* **Estimated Scope:** Large (4+ hours)

---

#### API-007: Validate vehicle IDs, scenario names, and contact emails in session payloads

* **Priority:** Medium
* **Type:** Bug
* **Files:** `backend/app/models/session.py:L36-66`, `backend/app/services/sessions.py:L375-384`
* **Problem:** Session payloads accept arbitrary `vehicleId`, `scenario`, and `contactEmail` values without validation or length bounds.
* **Impact:** Invalid sessions can be persisted, analytics can skew, and DB bloat/garbage data accumulates.
* **Acceptance Criteria:**

  * [ ] `vehicleId` values are validated against the catalog; unknown IDs return 422.
  * [ ] `scenario` is validated against defined scenarios.
  * [ ] `contactEmail` and freeform fields enforce format and max length limits.
* **Dependencies:** API-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

### Domain: Backend Data Layer

(Tasks related to `backend/app/db/*`, `backend/app/models/*`)

#### DB-001: Add minimal schema migration mechanism for SQLite (so security/schema changes are safe)

* **Priority:** Medium
* **Type:** Refactor
* **Files:** `backend/app/db/session.py:L9-20`, `backend/app/db/models.py:L1-48`
* **Problem:** DB schema is created via `metadata.create_all()` without migrations; adding columns safely (e.g., session access control) is fragile.
* **Impact:** Makes production upgrades risky; encourages “drop DB” workflows.
* **Acceptance Criteria:**

  * [ ] Migration approach chosen and implemented (Alembic **or** explicit SQLite `ALTER TABLE` migration steps on startup).
  * [ ] Documented process exists for schema change rollout.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Large (4+ hours)

---

#### DB-002: Add `session_secret_hash` column to SessionRecord for access control

* **Priority:** High
* **Type:** Security
* **Files:** `backend/app/db/models.py:L10-41`
* **Problem:** No place to persist an access-control secret for sessions.
* **Impact:** Blocks SEC-005 (protecting session PII).
* **Acceptance Criteria:**

  * [ ] `SessionRecord` has a nullable `session_secret_hash` (or similar) column.
  * [ ] DB migration/update path exists for existing SQLite DBs (per DB-001 approach).
* **Dependencies:** DB-001
* **Parallel Safe:** No (schema + migration coordination)
* **Estimated Scope:** Medium (1-4 hours)

---

#### DB-003: Add indexes for session and analytics query paths

* **Priority:** High
* **Type:** Performance
* **Files:** `backend/app/db/models.py:L60-93`
* **Problem:** `session_id`, `vehicle_id`, and `created_at` columns are unindexed, and analytics queries scan full tables.
* **Impact:** Analytics summary and session lookups degrade quickly as data grows.
* **Acceptance Criteria:**

  * [ ] Add indexes on `calculation_results.session_id`, `calculation_results.vehicle_id`, `calculation_results.created_at`.
  * [ ] Add indexes on `user_inputs.session_id` (and any other high-frequency lookup columns).
  * [ ] Migration path included (DB-001).
* **Dependencies:** DB-001
* **Parallel Safe:** No (schema + migration coordination)
* **Estimated Scope:** Medium (1-4 hours)

---

### Domain: Data Sync & Integrity

(Tasks related to `data/*.py` ↔ `shared/data/*.ts` synchronization)

#### DATA-001: Fix `GRID_UPGRADE` constant being commented out by missing newline

* **Priority:** Medium
* **Type:** Bug
* **Files:** `data/constants.py:L49-51`
* **Problem:** `CHARGER_COST = 300000` and the comment `# Grid upgrade costs` are on the same line, causing `GRID_UPGRADE` to be effectively commented out / not defined.
* **Impact:** Generator scripts and/or backend calculations may silently omit grid upgrade cost assumptions.
* **Acceptance Criteria:**

  * [ ] `CHARGER_COST` and the grid upgrade comment are on separate lines.
  * [ ] `GRID_UPGRADE` is defined and accessible to any generators/importers.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### DATA-002: Make vehicle catalog generator output compatible with TS `VehicleDetail` type

* **Priority:** High
* **Type:** Bug
* **Files:** `scripts/generate_vehicle_catalog_ts.py:L31-68`, `shared/types/tco.types.ts:L124-158`
* **Problem:** Generator `allowed_keys` includes fields not present in the TS `VehicleDetail` interface (e.g., `noise_pollution_per_km`, `battery_replacement_per_kw`), risking a “run generator → break TS build” workflow.
* **Impact:** High risk of data drift or broken builds during routine data updates.
* **Acceptance Criteria:**

  * [ ] `allowed_keys` exactly matches `VehicleDetail` fields (or `VehicleDetail` is updated to match intended output).
  * [ ] Running the generator produces TS that typechecks without manual edits.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### DATA-003: Separate generated constants from hand-maintained “future” constants

* **Priority:** Medium
* **Type:** Refactor
* **Files:** `shared/data/constants.ts:L1-120`, `scripts/generate_vehicle_catalog_ts.py:L94-137`
* **Problem:** `shared/data/constants.ts` claims it is auto-generated but includes a hand-maintained `FUTURE_CONSTANTS` section. Running the generator would overwrite manual edits.
* **Impact:** Guaranteed drift and accidental deletion of manual constants; unclear source of truth.
* **Acceptance Criteria:**

  * [ ] Generated output is written to a dedicated file (e.g., `shared/data/constants.generated.ts`) and never manually edited.
  * [ ] Manual future constants live in a separate file (e.g., `shared/data/constants.future.ts`) and are imported where needed.
  * [ ] Header comments accurately reflect generation policy.
* **Dependencies:** None
* **Parallel Safe:** No (touches data generation + shared imports)
* **Estimated Scope:** Medium (1-4 hours)

---

#### DATA-004: Add CI check to enforce data sync between Python and generated TS

* **Priority:** Medium
* **Type:** Test
* **Files:** `.github/workflows/data-sync-check.yml (new)`, `scripts/generate_vehicle_catalog_ts.py:L1-137`
* **Problem:** No automated enforcement that generated TS data matches Python sources.
* **Impact:** Drift can ship silently; audits become unreliable.
* **Acceptance Criteria:**

  * [ ] CI job runs the generator and fails if `git diff` shows changes in generated files.
  * [ ] Job output clearly shows which files differ.
* **Dependencies:** DATA-002, DATA-003
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### DATA-005: Standardize catalog versioning and cache invalidation behavior

* **Priority:** Medium
* **Type:** Refactor
* **Files:** `shared/data/vehicleCatalog.ts:L6-13`, `frontend/src/state/tcoStore.ts:L148-166`, `scripts/generate_vehicle_catalog_ts.py:L73-92`
* **Problem:** Catalog version exists but generator doesn’t manage it; cache invalidation relies on correct manual updates and assumes persisted overrides are safe to keep.
* **Impact:** Users can retain stale/invalid per-vehicle overrides across catalog changes.
* **Acceptance Criteria:**

  * [ ] Version bump workflow is explicit (manual bump documented or generator computes it deterministically).
  * [ ] On version mismatch, store rehydrate clears or validates `vehicleParamOverrides` keys that no longer exist in the new catalog.
* **Dependencies:** DATA-002
* **Parallel Safe:** No (touches generator + frontend persistence)
* **Estimated Scope:** Medium (1-4 hours)

---

#### DATA-006: Carbon price trajectories are all zero, making carbon cost a no-op

* **Priority:** Medium
* **Type:** Data
* **Files:** `data/scenarios.py:L175-221`, `shared/data/scenarios.ts:L58-73`
* **Problem:** All scenarios set `carbon_price_trajectory` to zeros, so `calculateCarbonCostYear()` always returns 0 regardless of other inputs.
* **Impact:** Carbon cost outputs are effectively disabled and can mask carbon-related regressions (including CALC-001).
* **Acceptance Criteria:**

  * [ ] Define non-zero carbon price trajectories for scenarios where carbon pricing is expected **or** explicitly document/remove carbon cost outputs when carbon pricing is disabled.
  * [ ] Generated TS data reflects the intended carbon price policy.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

### Domain: Security

(Cross-cutting security concerns)

#### SEC-001: Fix SPA static file path traversal in backend

* **Priority:** Critical
* **Type:** Security
* **Files:** `backend/app/main.py:L42-47`
* **Problem:** `serve_spa()` joins `frontend_dist / full_path` and serves the file if it exists, without restricting `full_path` from containing `..`.
* **Impact:** If `frontend/dist` exists, an attacker can potentially read arbitrary files on the server via crafted paths.
* **Acceptance Criteria:**

  * [ ] Requests containing traversal (e.g., `../`) cannot escape `frontend_dist`.
  * [ ] Use `StaticFiles` (recommended) or resolve-and-verify path containment before serving.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-002: Tighten CORS defaults and prevent unsafe `*` + credentials combinations

* **Priority:** High
* **Type:** Security
* **Files:** `backend/app/main.py:L20-27`, `backend/app/core/config.py:L28-44`
* **Problem:** CORS config allows `allow_methods=["*"]`, `allow_headers=["*"]`, with `allow_credentials=True`, and defaults origins to `http://localhost:5000` only.
* **Impact:** Over-broad CORS increases exposure; misconfigured defaults can break local dev or force developers to loosen CORS further.
* **Acceptance Criteria:**

  * [ ] Default origins include the actual dev ports in use (see DOC-003 alignment) and are configurable via env.
  * [ ] If `allow_credentials=True`, origins cannot be `*` (enforced by validation).
  * [ ] Methods/headers are restricted to what the frontend actually uses.
* **Dependencies:** DOC-003 (port decision)
* **Parallel Safe:** No (touches shared config decisions)
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-003: Add backend-side bounds checking for overrides and payload fields

* **Priority:** High
* **Type:** Security
* **Files:** `backend/app/models/calculation.py:L13-45`, `backend/app/models/session.py:L20-77`
* **Problem:** Backend accepts override payloads without numeric bounds (beyond type), enabling extreme values and oversized data.
* **Impact:** DoS risk (large payloads), stored corruption, and inconsistent behavior vs frontend validation.
* **Acceptance Criteria:**

  * [ ] Pydantic `Field(ge=..., le=...)` constraints added for override fields to match frontend `wizardForm.ts` ranges.
  * [ ] Invalid overrides return 422 with clear validation errors.
* **Dependencies:** FE-002 (range alignment), CALC-005 (engine clamping)
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-004: Add request size limits for session create/update endpoints

* **Priority:** Medium
* **Type:** Security
* **Files:** `backend/app/main.py:L1-70`
* **Problem:** No explicit request body size limits; sessions can store large blobs in SQLite.
* **Impact:** DoS via large payloads; DB bloat and performance degradation.
* **Acceptance Criteria:**

  * [ ] Middleware rejects requests over a defined max size (documented).
  * [ ] 413 response (or equivalent) returned for oversized payloads.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-005: Add session access-control secret for read/update to protect stored PII

* **Priority:** High
* **Type:** Security
* **Files:** `backend/app/db/models.py:L10-41`, `backend/app/services/sessions.py:L96-198`, `backend/app/api/router.py:L38-79`, `frontend/src/services/api.ts:L55-92`
* **Problem:** Sessions contain contact emails/notes and are accessible by knowing `sessionId` alone. There is no authentication or per-session secret.
* **Impact:** If a sessionId leaks (logs, screenshots, referrers), stored PII is exposed.
* **Acceptance Criteria:**

  * [ ] Session create returns a `sessionSecret` (only shown once).
  * [ ] GET/PUT endpoints require `sessionSecret` (header or query) and reject requests without it.
  * [ ] Server stores only a hash of the secret (not plaintext).
* **Dependencies:** API-001, DB-002
* **Parallel Safe:** No (touches router + DB + FE)
* **Estimated Scope:** Large (4+ hours)

---

#### SEC-006: Add automated dependency vulnerability scanning in CI

* **Priority:** Medium
* **Type:** Security
* **Files:** `.github/workflows/dependency-audit.yml (new)`
* **Problem:** Dependency vulnerability review cannot be verified from the provided repomix snapshot (package manifests not included). There is no enforced scanning shown in-repo.
* **Impact:** Known vulnerabilities can ship unnoticed; audit gaps persist.
* **Acceptance Criteria:**

  * [ ] CI runs `npm audit` (or equivalent) for frontend and `pip-audit` (or equivalent) for backend.
  * [ ] Pipeline fails on high/critical issues (policy documented).
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-007: Restrict analytics summary endpoint to backend-only access

* **Priority:** High
* **Type:** Security
* **Files:** `backend/app/api/router.py:L101-109`, `backend/app/main.py:L17-29`
* **Problem:** `/api/v1/analytics/summary` is publicly accessible with no auth despite being intended for internal backend-only use.
* **Impact:** Usage metrics can be scraped or abused; exposes operational data.
* **Acceptance Criteria:**

  * [ ] Analytics endpoint requires an internal auth mechanism (service token, admin API key, or network allowlist) or is removed from the public router.
  * [ ] Frontend cannot access analytics unless explicitly authorized.
* **Dependencies:** API-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### SEC-008: Add rate limiting for session and analytics endpoints

* **Priority:** Medium
* **Type:** Security
* **Files:** `backend/app/main.py:L17-29`, `backend/app/api/router.py:L60-109`
* **Problem:** No rate limiting exists on session create/update or analytics endpoints.
* **Impact:** Enables abuse (DoS, storage bloat) and noisy analytics.
* **Acceptance Criteria:**

  * [ ] Apply per-IP or per-session rate limits to POST/PUT `/sessions` and GET `/analytics/summary`.
  * [ ] Limits are configurable via settings and documented.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

### Domain: Testing

(Missing tests, test improvements)

#### TEST-001: Add regression test for diesel carbon cost efficiency improvements

* **Priority:** Medium
* **Type:** Test
* **Files:** `frontend/src/test/calculator/scenarios.test.ts:L1-116`
* **Problem:** Scenario tests don’t explicitly assert diesel carbon costs respond to diesel efficiency improvements.
* **Impact:** CALC-001 can regress without detection.
* **Acceptance Criteria:**

  * [ ] New assertion compares diesel `carbon_cost` under baseline vs a scenario with improved diesel efficiency and confirms decrease.
* **Dependencies:** CALC-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### TEST-002: Update math tests to match the unified PV convention

* **Priority:** Medium
* **Type:** Test
* **Files:** `frontend/src/test/calculator/math.test.ts:L1-59`, `shared/calculator/math.ts:L14-28`
* **Problem:** Tests validate current `calculatePresentValue()` behavior; after CALC-003 the expected PV should reflect the chosen convention.
* **Impact:** Prevents PV-convention drift.
* **Acceptance Criteria:**

  * [ ] Tests updated/added so `calculatePresentValue` and the PV method used in TCO align with documented convention.
* **Dependencies:** CALC-003
* **Parallel Safe:** No (same area as CALC-003)
* **Estimated Scope:** Small (< 1 hour)

---

#### TEST-003: Add edge-case test ensuring invalid range override cannot produce NaN/Infinity

* **Priority:** Medium
* **Type:** Test
* **Files:** `frontend/src/test/calculator/edge-cases.test.ts:L1-76`
* **Problem:** No test ensures `range_km_override=0` is rejected/handled safely.
* **Impact:** Division-by-zero regressions can slip into production.
* **Acceptance Criteria:**

  * [ ] Test sets `vehicleParamOverrides[<bevId>].range_km_override = 0` and asserts all numeric outputs (`total_cost`, `annual_cost`, `cost_per_km`) are finite.
* **Dependencies:** CALC-004, FE-002
* **Parallel Safe:** No (depends on calculator behavior)
* **Estimated Scope:** Small (< 1 hour)

---

#### TEST-004: Add backend smoke tests for router startup and core endpoints

* **Priority:** High
* **Type:** Test
* **Files:** `tests/test_api_smoke.py (new)`, `backend/app/api/router.py:L1-89`
* **Problem:** Backend test suite is effectively empty (`tests/conftest.py` only). Router currently has import breakage.
* **Impact:** Critical runtime failures can ship undetected.
* **Acceptance Criteria:**

  * [ ] Tests start the FastAPI app and hit `/api/v1/health`, `/api/v1/sessions` create, and `/api/v1/analytics/summary`.
  * [ ] Responses validate expected JSON keys (camelCase).
* **Dependencies:** API-001
* **Parallel Safe:** No (depends on router)
* **Estimated Scope:** Medium (1-4 hours)

---

#### TEST-005: Add backend unit test covering session override normalization

* **Priority:** Medium
* **Type:** Test
* **Files:** `tests/test_session_overrides_shape.py (new)`, `backend/app/services/sessions.py:L299-319`
* **Problem:** `_replace_inputs` risks writing malformed override shapes.
* **Impact:** Session restore bugs can persist unnoticed.
* **Acceptance Criteria:**

  * [ ] Test updates a session with vehicle overrides and confirms `wizard_state["vehicleParamOverrides"]` shape matches frontend expectations.
* **Dependencies:** API-003
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### TEST-006: Add security regression test for SPA path traversal

* **Priority:** High
* **Type:** Test
* **Files:** `tests/test_spa_path_traversal.py (new)`, `backend/app/main.py:L42-47`
* **Problem:** No automated coverage for traversal vulnerability.
* **Impact:** High-severity regression risk.
* **Acceptance Criteria:**

  * [ ] Test requests a traversal path and asserts it does not return non-frontend files and does not respond 200 with sensitive content.
* **Dependencies:** SEC-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### TEST-007: Align Playwright baseURL with the chosen frontend dev port

* **Priority:** Low
* **Type:** Test
* **Files:** `frontend/playwright.config.ts:L1-15`
* **Problem:** Playwright `baseURL` is hardcoded to `http://localhost:5001`, which does not match the documented/dev ports.
* **Impact:** E2E tests fail to run without manual port edits.
* **Acceptance Criteria:**

  * [ ] `baseURL` matches the standardized frontend port chosen in DOC-003.
  * [ ] E2E tests run against the same port used by `bun run dev`.
* **Dependencies:** DOC-003
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

### Domain: Documentation & Configuration

(Docs, config files, build setup)

#### DOC-001: Update API.md to match actual FastAPI schemas and response casing

* **Priority:** High
* **Type:** Documentation
* **Files:** `API.md:L36-217`, `backend/app/models/session.py:L20-170`
* **Problem:** API.md documents outdated endpoints and snake_case response fields that do not match alias-based responses (`sessionId`, `wizardData`, etc.).
* **Impact:** Integrators and internal devs will build against the wrong contract; increases support burden.
* **Acceptance Criteria:**

  * [ ] API.md reflects current endpoints in `backend/app/api/router.py`.
  * [ ] Example requests/responses match actual casing and schema fields.
* **Dependencies:** API-001
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### DOC-002: Remove or replace references to missing DEPLOYMENT/TROUBLESHOOTING docs

* **Priority:** Low
* **Type:** Documentation
* **Files:** `README.md:L235-249`, `AGENTS.md:L34-47`
* **Problem:** README/AGENTS reference `DEPLOYMENT.md` and `TROUBLESHOOTING.md` which do not exist.
* **Impact:** Onboarding friction; signals stale documentation.
* **Acceptance Criteria:**

  * [ ] Either create the referenced files with minimal useful content **or** remove links and replace with accurate sections.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### DOC-003: Standardize dev ports and update CORS/compose/vite/docs accordingly

* **Priority:** Medium
* **Type:** Documentation
* **Files:** `frontend/vite.config.ts:L6-18`, `docker-compose.yml:L16-35`, `backend/app/core/config.py:L28-44`, `README.md:L81-118`
* **Problem:** Vite is configured for port 5000, docker-compose maps frontend to 3000, backend CORS defaults to 5000, and README states 5000—these are inconsistent.
* **Impact:** Dev environments break or prompt insecure CORS loosening; wasted setup time.
* **Acceptance Criteria:**

  * [ ] Single chosen frontend dev port is reflected in Vite config, docker-compose, backend CORS defaults, and README.
  * [ ] `docker compose up` produces a working frontend→backend flow without manual port edits.
* **Dependencies:** SEC-002
* **Parallel Safe:** No (cross-file consistency)
* **Estimated Scope:** Medium (1-4 hours)

---

#### DOC-004: Fix README claims about parity/verification tests and missing archive references

* **Priority:** Medium
* **Type:** Documentation
* **Files:** `README.md:L165-226`, `replit.md:L34-43`
* **Problem:** README references `verification.test.ts` and an archived Python reference engine that is not present in the provided repo snapshot.
* **Impact:** Misleads contributors; suggests missing test coverage that doesn’t exist.
* **Acceptance Criteria:**

  * [ ] README only references tests that exist in `frontend/src/test/*`.
  * [ ] Any mention of archive/reference engine is updated or removed, with pointers to actual code if it exists elsewhere.
* **Dependencies:** None
* **Parallel Safe:** Yes
* **Estimated Scope:** Small (< 1 hour)

---

#### DOC-005: Document the data generation workflow and “source of truth” policy

* **Priority:** Low
* **Type:** Documentation
* **Files:** `AGENTS.md:L6-20`, `scripts/generate_vehicle_catalog_ts.py:L1-137`, `shared/data/constants.ts:L1-20`
* **Problem:** It’s unclear which data is authoritative and how to regenerate TS data without breaking manual additions.
* **Impact:** Drift risk and blocked updates.
* **Acceptance Criteria:**

  * [ ] Document: Python data as source, how to run generator(s), which TS files are generated, and how versioning works.
  * [ ] Include a “do not edit generated files” rule that matches actual layout after DATA-003.
* **Dependencies:** DATA-003
* **Parallel Safe:** Yes
* **Estimated Scope:** Medium (1-4 hours)

---

#### DOC-006: Clarify discounting convention and cost breakdown units in code + UI copy

* **Priority:** Medium
* **Type:** Documentation
* **Files:** `shared/calculator/math.ts:L5-16`, `shared/types/tco.types.ts:L82-105`, `frontend/src/components/results/CostBreakdownChart.tsx:L32-35`
* **Problem:** Comments and UI copy imply a PV-only interpretation, but implementation and types explicitly mix bases.
* **Impact:** Stakeholder trust risk; audit defensibility weakened.
* **Acceptance Criteria:**

  * [ ] Discounting convention is explicitly documented (e.g., whether year-1 cashflows are discounted).
  * [ ] Cost breakdown fields include unit annotations (PV vs nominal vs upfront) or the UI is updated to avoid incorrect claims.
* **Dependencies:** CALC-003, VIZ-002
* **Parallel Safe:** No (depends on conventions chosen)
* **Estimated Scope:** Medium (1-4 hours)

---

## Dependency Graph

Critical Path:

* **SEC-001 → API-001 → TEST-004**
* **CALC-002 → VIZ-002 → DOC-006**
* **DB-001 → DB-002 → SEC-005**

Parallel Workstreams:

* **Stream A (Backend viability & security):** SEC-001, API-001 → API-002, SEC-004, TEST-006
* **Stream B (Calculator correctness):** CALC-001, CALC-002, CALC-003, CALC-004, CALC-005, TEST-001/002/003
* **Stream C (Frontend UX & charts):** FE-002 → FE-003, VIZ-001/002/003/004
* **Stream D (Data integrity):** DATA-001, DATA-002 → DATA-003 → DATA-004, DATA-005, DOC-005
* **Stream E (Docs):** DOC-001, DOC-002, DOC-003, DOC-004 (mostly parallel, with DOC-001 depending on API-001)

---

## Priority Matrix

| Priority | Count | Domains Affected                                                    |
| -------- | ----- | ------------------------------------------------------------------- |
| Critical | 2     | Security, Backend API                                               |
| High     | 10    | Calculator, Visualization, API, Security, Testing                   |
| Medium   | 15    | Calculator, Frontend State, API, Data Sync, Security, Testing, Docs |
| Low      | 8     | Calculator, Frontend State, Visualization, API, Docs                |

---

## Suggested Execution Order

### Phase 1: Critical Fixes (Sequential)

1. **SEC-001** – Fix SPA path traversal (`backend/app/main.py`)
2. **API-001** – Fix router imports/wiring so backend starts
3. **TEST-004** – Backend smoke tests to lock the baseline

### Phase 2: High Priority (Parallel Streams)

* **Stream A (Security hardening):** SEC-002, SEC-003, SEC-004
* **Stream B (Calculator correctness):** CALC-001, CALC-002, CALC-003, CALC-004
* **Stream C (Charts correctness):** VIZ-001, VIZ-002, VIZ-003
* **Stream D (Data integrity):** DATA-001, DATA-002

### Phase 3: Medium Priority (Parallel)

* **Frontend robustness:** FE-004, FE-005, FE-006
* **Tests:** TEST-001, TEST-002, TEST-003, TEST-005, TEST-006
* **Docs/config alignment:** DOC-003, DOC-006, DOC-001

### Phase 4: Low Priority / Cleanup

* CALC-006, CALC-007
* FE-001, FE-007
* VIZ-004, VIZ-005
* DOC-002, DOC-004, DOC-005
* SEC-006 (CI scanning), API-004, API-005

---
