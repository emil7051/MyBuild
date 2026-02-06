# Frontend Chart Conventions (updated 2026-02-06)

Results charts in `frontend/src/components/results/` must respect grouped cost-basis semantics.

`CostBreakdown` groups:
- `npv_costs` (discounted): fuel, maintenance, battery replacement, carbon, charging labour, payload penalty, residual value.
- `nominal_costs` (non-discounted totals): insurance, registration, financing, depreciation.
- `upfront_costs`: purchase cost and taxes/fees.

Important interpretation rules:
- Do not describe every breakdown field as present-value; basis is mixed across groups.
- `financing_cost` is a nominal total interest figure in `nominal_costs` (not an upfront component).
- `total_cost` in `CalculationResponsePayload` remains the authoritative NPV-adjusted comparison metric.

Payback chart notes:
- Uses year-by-year nominal cumulative timelines from `calculateNominalCostTimeline`.
- Interpolates payback crossing between yearly points when BEV overtakes diesel.