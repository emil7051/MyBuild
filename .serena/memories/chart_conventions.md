# Frontend Chart Conventions

The frontend results charts in `frontend/src/components/results/` have specific patterns.

## Value Type Awareness (IMPORTANT)

The `CostBreakdown` type has MIXED value bases - see `shared/types/tco.types.ts` for full documentation:

### NPV-adjusted fields
- fuel_cost
- maintenance_cost
- battery_replacement_cost
- carbon_cost
- charging_labour_cost
- payload_penalty_cost
- residual_value

### Nominal lifetime totals (NOT discounted)
- insurance_cost
- registration_cost
- depreciation

### Upfront values (year 0)
- purchase_cost
- financing_cost (total loan interest, NOT upfront!)
- taxes_and_fees

**Key insight**: Do NOT claim all breakdown values are "present value" - they are mixed. UI labels must reflect this.

## PaybackChart (`PaybackChart.tsx`)

- Uses `purchase_cost` only for upfront (NOT financing_cost)
- `financing_cost` is total nominal interest over loan term, not an upfront payment
- Interpolates payback year with slope guard against division by zero
- Subtitle: "Cumulative cost comparison (upfront purchase + annual operating costs)"

## SavingsWaterfallChart (`SavingsWaterfallChart.tsx`)

- BEV selection is deterministic: selects BEV with lowest `total_cost`
- Financing is excluded from breakdown categories (mixed units would confuse)
- Total savings bar uses `total_cost` comparison which IS NPV-adjusted
- Comment explains why financing is excluded

## CostBreakdownChart (`CostBreakdownChart.tsx`)

- Subtitle: "Stacked view of lifetime cost components" (NOT "present value")
- Stacks all breakdown fields for visual comparison
- Individual values have mixed bases but directional insights are valid

## Total Cost

The `total_cost` in `CalculationResponsePayload` IS fully NPV-adjusted and represents the true economic comparison. Use this for headline comparisons.
