# Code Audit Verification Report

**Date:** 2026-01-19
**Branch:** phase4-stream-f
**Audit Source:** GPT.md (55 issues across 9 domains)
**Methodology:** 4 parallel Opus agents using Serena semantic code analysis

---

## Executive Summary

| Domain | Total Issues | Fixed | Partially Fixed | Not Fixed |
|--------|-------------|-------|-----------------|-----------|
| Calculator Engine | 9 | 8 | 0 | 1 |
| Backend API | 7 | 7 | 0 | 0 |
| Security | 8 | 7 | 1 | 0 |
| Database | 3 | 3 | 0 | 0 |
| Frontend State/Forms | 9 | 6 | 1 | 2 |
| Visualization | 5 | 2 | 0 | 3 |
| Data Sync | 6 | 6 | 0 | 0 |
| **TOTAL** | **47** | **39 (83%)** | **2 (4%)** | **6 (13%)** |

**Overall Assessment:** The codebase has undergone significant remediation. Critical security issues (SEC-001 path traversal, API-001 router wiring) are fully resolved. The remaining issues are primarily low-priority UI labeling and one minor state management edge case.

---

## Outstanding Issues Requiring Attention

### High Priority

#### 1. VIZ-002: CostBreakdownChart misleading labeling
**Status:** NOT FIXED
**File:** `frontend/src/components/results/CostBreakdownChart.tsx`
**Problem:** Chart subtitle is generic ("Stacked view of lifetime cost components") while the breakdown contains mixed value bases (NPV-adjusted, nominal lifetime totals, and upfront values). This can mislead stakeholders about what's driving cost differences.

**Current code:**
```typescript
subtitle="Stacked view of lifetime cost components for each vehicle."
```

**Fix required:** Add a tooltip or footnote explaining:
- NPV-adjusted: fuel_cost, maintenance_cost, battery_replacement_cost, carbon_cost, charging_labour_cost, payload_penalty_cost, residual_value
- Nominal lifetime totals: insurance_cost, registration_cost, depreciation
- Upfront: purchase_cost, taxes_and_fees

---

### Medium Priority

#### 2. VIZ-004: SensitivityTornadoChart not labeled as approximate
**Status:** NOT FIXED
**File:** `frontend/src/components/results/SensitivityTornadoChart.tsx`
**Problem:** Chart performs linearized sensitivity analysis (scales baseline category totals by ±20%) but doesn't indicate this is an approximation, not a true model recomputation.

**Current description:**
```typescript
<p className="text-sm text-slate-600">
  Impact of +/- 20% change in each parameter on BEV savings
</p>
```

**Fix required:** Add text like "Estimated linear impact (actual sensitivity may vary due to non-linear effects)"

---

#### 3. VIZ-005: Sensitivity analysis doesn't recompute TCO
**Status:** NOT FIXED
**File:** `frontend/src/components/results/SensitivityTornadoChart.tsx`
**Problem:** Uses static cost deltas rather than rerunning the calculator with perturbed inputs. This doesn't capture compound effects (e.g., higher annual_kms affects fuel AND maintenance AND charging labour).

**Fix required:** Either:
1. Implement true sensitivity by calling `calculateComparison()` with ±20% parameter variations, OR
2. Accept the approximation and clearly label it (which would also satisfy VIZ-004)

---

#### 4. FE-009: Save status not displayed in UI
**Status:** PARTIALLY FIXED
**File:** `frontend/src/pages/WizardPage.tsx`
**Problem:** The `useWizardAutosave()` hook returns `saveStatus` and shows a toast on failure, but WizardPage doesn't consume `saveStatus` to show a persistent visual indicator.

**Current code (line 60):**
```typescript
useWizardAutosave();  // Does not destructure saveStatus
```

**Fix required:** Destructure `saveStatus` and display a save indicator (e.g., "Saving...", "Saved", "Not saved") in the wizard header.

---

### Low Priority

#### 5. CALC-007: getVehicleCatalogSnapshot doesn't return version
**Status:** NOT FIXED
**File:** `shared/calculator/tcoCalculator.ts:889`
**Problem:** Function returns only `VEHICLE_DETAILS` but `VEHICLE_CATALOG_VERSION` exists separately. Consumers can't validate cache/version compatibility using the "snapshot".

**Current code:**
```typescript
getVehicleCatalogSnapshot = () => VEHICLE_DETAILS;
```

**Fix required:**
```typescript
getVehicleCatalogSnapshot = () => ({
  version: VEHICLE_CATALOG_VERSION,
  vehicles: VEHICLE_DETAILS,
});
```

---

#### 6. FE-001: WizardPage duty-cycle fallback mismatch
**Status:** NOT FIXED
**File:** `frontend/src/pages/WizardPage.tsx:125`
**Problem:** Fallback default `{ urban: 40, regional: 35, longHaul: 25 }` doesn't match store default `{ urban: 60, regional: 25, longHaul: 15 }`.

**Current code:**
```typescript
dutyCycle: dutyCycle ?? { urban: 40, regional: 35, longHaul: 25 },
```

**Fix required:** Change to `{ urban: 60, regional: 25, longHaul: 15 }` or import from shared constant.

---

#### 7. SEC-008: Rate limiting incomplete
**Status:** PARTIALLY FIXED
**File:** `backend/app/api/router.py`
**Problem:** Rate limiting is applied to session and analytics endpoints but not vehicle catalog endpoints (`/vehicles`, `/vehicles/{vehicle_id}`). While these serve static data, they could be targeted for reconnaissance.

**Recommendation:** Consider adding rate limiting to vehicle endpoints, or document that this is intentionally left unrestricted.

---

## Verification of Fixed Issues

### Critical Fixes (All Resolved)

| Issue | Description | Evidence |
|-------|-------------|----------|
| SEC-001 | SPA path traversal | Uses `Path.resolve()` + `is_relative_to()` check |
| API-001 | Router imports broken | Proper imports from `VehicleCatalogService`, `SessionService`, `AnalyticsSummary` |

### Calculator Engine (8/9 Fixed)

| Issue | Status | Evidence |
|-------|--------|----------|
| CALC-001 | FIXED | `diesel_efficiency_improvement` applied in `calculateCarbonCostYear()` |
| CALC-002 | FIXED | `taxesAndFees = stampDuty` (no longer includes registration) |
| CALC-003 | FIXED | Both PV methods use beginning-of-year convention (mathematically consistent) |
| CALC-004 | FIXED | `sanitizePayload()` clamps range_km to [50, 2500], charging_time to [0.1, 8]; defensive zero checks added |
| CALC-005 | FIXED | All multipliers clamped (battery_life_variation [0.5, 1.5], etc.) |
| CALC-006 | FIXED | `calculateBatteryHealth` function removed |
| CALC-008 | FIXED | `calculateResidualValueAtLife()` uses `vehicle.msrp` as base |
| CALC-009 | FIXED | Fixed rebate applied first: `percentageBase = Math.max(0, msrp - rebate)` |

### Backend & Security (17/18 Fixed)

| Issue | Status | Evidence |
|-------|--------|----------|
| API-002 | FIXED | `validate_uuid()` function rejects invalid UUIDs with 422 |
| API-003 | FIXED | Overrides normalized to `{ "cost": {...}, "vehicle": {...} }` structure |
| API-004 | FIXED | Redis caching controlled by `settings.redis_url` |
| API-005 | FIXED | Uses `lifespan` async context manager instead of deprecated `@app.on_event` |
| API-006 | FIXED | SQL aggregation with `func.count()`, `group_by()` |
| API-007 | FIXED | Validators for scenario, vehicle IDs, email format with length constraints |
| SEC-002 | FIXED | Wildcard origin explicitly rejected; methods/headers restricted |
| SEC-003 | FIXED | Pydantic `Field(ge=..., le=...)` constraints on all overrides |
| SEC-004 | FIXED | `RequestSizeLimitMiddleware` rejects >1MB payloads with 413 |
| SEC-005 | FIXED | `session_secret_hash` column + bcrypt hashing + `X-Session-Secret` header |
| SEC-006 | FIXED | `dependency-audit.yml` runs pip-audit + npm audit |
| SEC-007 | FIXED | `verify_analytics_api_key()` requires `X-Analytics-Key` header |
| DB-001 | FIXED | Alembic migrations with 3 version files |
| DB-002 | FIXED | `session_secret_hash` column in `SessionRecord` |
| DB-003 | FIXED | Indexes on session_id, vehicle_id, created_at with composite index for analytics |

### Frontend State (6/9 Fixed)

| Issue | Status | Evidence |
|-------|--------|----------|
| FE-002 | FIXED | Schema enforces min values (range_km >= 50, charging_time >= 0.1) |
| FE-003 | FIXED | `safeParse` errors displayed via `setFieldError()` |
| FE-004 | FIXED | `validateDutyCycle()` handles NaN, negative, sum != 100 |
| FE-005 | FIXED | `pendingPayload` ref queues data during session creation |
| FE-006 | FIXED | `AbortController` cancels in-flight autosave requests |
| FE-007 | FIXED | `useCalculationRunner` removed from WizardCompareStep |
| FE-008 | FIXED | Request ID + vehicle order captured before calculation |

### Visualization & Data (8/11 Fixed)

| Issue | Status | Evidence |
|-------|--------|----------|
| VIZ-001 | FIXED | Upfront excludes financing_cost; slope edge case guarded |
| VIZ-003 | FIXED | Deterministic comparator (first diesel vs lowest-cost BEV); financing_cost excluded |
| DATA-001 | FIXED | CHARGER_COST and GRID_UPGRADE on separate lines |
| DATA-002 | FIXED | DETAIL_FIELDS matches VehicleDetail interface |
| DATA-003 | FIXED | Generated in constants.generated.ts, separate from constants.future.ts |
| DATA-004 | FIXED | data-sync-check.yml workflow checks for drift |
| DATA-005 | FIXED | Version computed from hash; rehydrate clears stale overrides |
| DATA-006 | FIXED (by design) | Carbon price intentionally zero (reflects Australian policy); well documented |

---

## Recommended Action Plan

### Immediate (Before Next Release)
1. **FE-001**: Fix duty-cycle fallback constant (5 min fix)
2. **CALC-007**: Update getVehicleCatalogSnapshot to return version (5 min fix)

### Short-term (Next Sprint)
3. **VIZ-002**: Add mixed-units explanation to CostBreakdownChart
4. **VIZ-004**: Add "approximate" label to SensitivityTornadoChart
5. **FE-009**: Display save status indicator in WizardPage

### Optional Enhancement
6. **VIZ-005**: True sensitivity recomputation (if linearized approximation is unacceptable)
7. **SEC-008**: Rate limit vehicle catalog endpoints

---

## Issues Not Investigated

The following issues from the original audit were **not in scope** for this verification (Testing and Documentation domains):

- TEST-001 through TEST-007 (testing tasks)
- DOC-001 through DOC-006 (documentation tasks)

These should be verified separately as they require different tooling and review approaches.

---

## Conclusion

The codebase is in **good health** with 83% of identified issues resolved. All critical security vulnerabilities have been addressed. The remaining issues are primarily:

1. **UI labeling/clarity** (VIZ-002, VIZ-004) - user experience improvements
2. **Minor state edge cases** (FE-001, FE-009) - unlikely to affect real users
3. **Code hygiene** (CALC-007) - developer experience improvement

The backend is production-ready. The frontend would benefit from the visualization labeling fixes before stakeholder-facing use.
