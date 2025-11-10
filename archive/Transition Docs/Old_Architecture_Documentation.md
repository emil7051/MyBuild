# Old Architecture Documentation

This document preserves the reference architecture for the original Python TCO calculation engine so future contributors can understand legacy behaviour even though the active roadmap now lives entirely inside `TRANSFORMATION_MASTER_PLAN.md` and the execution log.

## System Overview

```
┌─────────────────────────────── User Inputs ───────────────────────────────┐
│ Vehicle selection │ Scenario selection │ Operating & cost overrides       │
└──────────────┬────────────────────────────────────────────────────────────┘
               │
        ┌──────▼──────┐   Prefetch specs + policies from `data/*`
        │VehicleInputs│   (stamp duty, financing, base costs)
        └──────┬──────┘
               │ feeds calculators
   ┌───────────┼──────────────────────────────────────────────────────────┐
   │ Financial │ Operating │ Scenario adjustments (policies, trajectories)│
   └────┬──────┴──────┬────────────────────────────────────────────────────┘
        │             │
        ▼             ▼
   Year-by-year loops (15 years) applying price multipliers, efficiency curves,
   payload penalties, battery replacement, and residual value calculations.
               │
               ▼
         NPV aggregation → `TCOResult` (14 cost components + metadata)
```

FastAPI now wraps this engine, but the logical flow above still drives every parity discussion.

## Cost Component Reference (14 items)
- **Purchase Costs (Year 0)**: purchase_cost, financing_cost, depreciation, taxes_and_fees.
- **Operating Costs (Years 1‑15, discounted)**: fuel_cost, maintenance_cost, insurance_cost, registration_cost, battery_replacement_cost, carbon_cost, charging_labour_cost, payload_penalty_cost.
- **Residual Value (Year 15)**: residual_value reduces total cost when discounted to present value.

## Codebase Structure Snapshot

```
MyBuild/
├── calculations/          # Engine modules (~2000 lines total)
│   ├── calculations.py    # Main orchestration (calculate_tco_from_inputs, comparisons)
│   ├── financial.py       # Stamp duty, rebates, financing, depreciation
│   ├── operating.py       # Fuel, maintenance, insurance, battery, carbon, payload logic
│   ├── inputs.py          # VehicleInputs builder + cached calculator helpers
│   ├── simulation.py      # Monte Carlo + sensitivity analysis utilities
│   ├── utils.py           # Shared financial math helpers
│   └── __init__.py        # Exports for CLI + services
├── data/
│   ├── constants.py / policies.py / scenarios.py  # Economic assumptions & policy toggles
│   ├── vehicles.py + vehicle_models.csv          # 16 VehicleModel definitions with pairs
│   └── __init__.py
├── analysis/              # Research & reporting scripts (payback, policy impact, timeline)
├── output/                # Plotly/CSV exporters invoked by `main.py`
├── scripts/               # Generators (e.g., vehicle catalog for TS clients)
├── tests/                 # pytest suite (`test_comprehensive.py` references DataValidator)
└── main.py                # CLI driver for batch exports
```

## Key Data Structures
- **`VehicleModel`** (defined in `data/vehicles.py`): 17 immutable fields covering IDs, payload, MSRP, range, battery, consumption, maintenance, registration, and default annual kms. Each BEV has a `comparison_pair` diesel counterpart.
- **`VehicleInputs`** (`calculations/inputs.py`): Pre-computes stamp duty, financing details, base fuel/maintenance/insurance, and exposes helpers that apply scenario multipliers for each year.
- **`TCOResult`** (`calculations/calculations.py`): Stores total/annual cost, cost per km, and the 14 component breakdowns so downstream tools (FastAPI, reports, analysis scripts) can consume consistent payloads.

## Calculation Flow Highlights
1. **Input Normalisation** – Map user inputs + selected vehicle/scenario into `VehicleInputs`, including policy incentives and base financial setup (down payment, loan amount, discount rate, utilisation).
2. **Annual Loop (Years 1‑15)** – For each year calculate fuel/electricity spend, maintenance, insurance, registration, carbon, charging labour, payload penalties, and BEV battery replacement (year 8) while applying scenario price/efficiency trajectories.
3. **Present Value Math** – Discount all annual costs using the 5 % rate, add upfront purchase/financing, subtract discounted residual value, then derive annual cost and cost-per-km metrics.
4. **Scenario & Monte Carlo Hooks** – `simulation.py` exposes `MonteCarloSimulation` and `SensitivityAnalysis` with override keys such as `fuel_price_variation`, `annual_kms_variation`, `battery_life_variation`, ensuring the web experience can mirror today’s research workflows.

## Supporting Analytics Assets
- `analysis/analysis.py`, `analysis/generate_tco_analysis.py`, and `analysis/purchase_year_analysis.py` loop over vehicles, purchase years, and scenarios to produce CSV/JSON/Plotly artefacts that TWU policy teams use today.
- `output/charts.py` and `output/generate_html_report.py` bundle the same data into presentation-ready dashboards; FastAPI must eventually expose equivalent exports or scheduled jobs.

Keep this document unchanged unless the legacy Python implementation itself evolves; new platform decisions belong in the master plan and execution log.
