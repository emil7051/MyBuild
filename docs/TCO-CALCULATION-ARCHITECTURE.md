# TCO Calculation Engine: Comprehensive Architecture & Calculation Map

## 1. System Architecture Overview

```
+---------------------+       +-----------------------+       +------------------+
|  Python Data Layer   | ----> | Code Generation       | ----> | TypeScript Data  |
|  data/*.py           |       | scripts/generate_*.py |       | shared/data/*.ts |
|  (source of truth)   |       |                       |       | (auto-generated) |
+---------------------+       +-----------------------+       +------------------+
                                                                       |
                                                                       v
+---------------------+       +-----------------------+       +------------------+
|  Browser (React)     | <---- | Shared Calculator     | <---- | Financial Math   |
|  frontend/src/       |       | shared/calculator/    |       | shared/calculator|
|  Charts, wizard, UX  |       | tcoCalculator.ts      |       | /math.ts         |
+---------------------+       +-----------------------+       +------------------+
         |
         | (persist results only)
         v
+---------------------+
|  FastAPI Backend     |
|  backend/app/        |
|  Sessions, analytics |
+---------------------+
```

**Key architectural decision:** All TCO calculations run client-side in the browser via the shared TypeScript engine. The backend never performs calculations. It receives pre-computed results for session persistence and analytics aggregation.

---

## 2. File Inventory

### Calculator Engine (`shared/calculator/`)

| File | Lines | Purpose |
|------|-------|---------|
| `tcoCalculator.ts` | ~987 | Core engine: all cost formulas, input sanitisation, orchestration |
| `math.ts` | ~96 | NPV functions: annuity PV, single-amount discounting, monthly payment NPV |
| `index.ts` | ~10 | Public API: exports `calculateTco`, `calculateComparison`, `calculateNominalCostTimeline` |
| `verification_data.json` | ~3,874 | 101 test fixtures from the Python reference implementation |

### Data Layer (`data/` Python, `shared/data/` TypeScript)

| Python Source | Generated TypeScript | Content |
|---------------|---------------------|---------|
| `data/vehicles.py` | `shared/data/vehicleCatalog.ts` | 16 vehicle specs (8 BEV, 8 Diesel) |
| `data/constants.py` | `shared/data/constants.generated.ts` | All numeric constants |
| `data/scenarios.py` | `shared/data/scenarios.ts` | 3 scenario definitions with 15-year trajectories |
| `data/policies.py` | `shared/data/policies.ts` | 6 policy incentive types (all disabled by default) |
| -- | `shared/data/constants.future.ts` | Manually maintained placeholder for planned features (currently empty) |

### Types (`shared/types/`)

| File | Content |
|------|---------|
| `tco.types.ts` | All interfaces: request/response payloads, cost breakdowns, vehicle types |
| `dutyCycle.ts` | Duty cycle validation logic and default values |

---

## 3. Entry Points and Calculation Flow

### Three Public Functions

1. **`calculateTco(payload: CalculationRequestPayload)`** -- single vehicle TCO
2. **`calculateComparison(payload: ComparisonRequestPayload)`** -- multiple vehicles (maps over `vehicle_ids`, calls `calculateTco` for each)
3. **`calculateNominalCostTimeline(payload: CalculationRequestPayload)`** -- year-by-year nominal costs for payback charts

### Internal Orchestration (`calculateTcoWithDetails`)

```
1. Sanitise payload (clamp overrides to defined limits, validate duty cycle)
2. Look up vehicle from catalog, apply vehicle parameter overrides
3. Resolve annual kms (override or vehicle default)
4. Normalise vehicle fields (replace NaN/undefined with fallbacks)
5. Calculate initial cost (MSRP + stamp duty - BEV rebates)
6. Build financing snapshot (down payment, loan amount, monthly payment, NPV of payments)
7. Calculate annual insurance and registration (constant across years)
8. Calculate annual charging labour cost (BEV only, constant across years)
9. Calculate annual payload penalty (constant across years)
10. FOR EACH YEAR 1-15:
    - Calculate fuel/energy cost (with scenario trajectory)
    - Calculate battery replacement cost (year 8 only)
    - Calculate carbon cost (with scenario trajectory)
    - Calculate maintenance cost (with scenario trajectory)
11. Compute NPV of each annual cost stream
12. Compute residual value at end of life, discount to present
13. Sum total_cost, derive annual_cost and cost_per_km
14. Assemble CostBreakdown struct
```

---

## 4. All 14 Cost Components: Formulas

### 4.1 Initial Cost and Purchase

```
stamp_duty = MSRP * 0.03
```

For BEVs with stamp duty exemption policy enabled:
```
stamp_duty = MSRP * 0.03 * (1 - exemption_percentage)
```

BEV rebate calculation (applied in order):
```
rebate = 0
if purchase_rebate.enabled:   rebate += fixed_amount
if percentage_rebate.enabled:
    base = max(0, MSRP - rebate)
    pct_rebate = base * percentage
    if max_amount: pct_rebate = min(pct_rebate, max_amount)
    rebate += pct_rebate
```

```
initial_cost = MSRP + stamp_duty - rebate
```

### 4.2 Financing

**If outright purchase:**
```
upfront_cost = initial_cost
financing_cost = 0
npv_purchase = initial_cost
```

**If financed:**
```
down_payment = initial_cost * 0.20
loan_amount = initial_cost - down_payment
effective_rate = base_rate (0.06) - green_loan_reduction (BEV only)
monthly_rate = effective_rate / 12
num_payments = 5 years * 12 = 60

monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate)^(-60))
total_payments = monthly_payment * 60
financing_cost = total_payments - loan_amount  (total nominal interest)

npv_purchase = down_payment + SUM[month=1..60](monthly_payment / (1 + 0.05)^(month/12))
```

### 4.3 Fuel/Energy Cost (per year, years 1-15)

**Diesel:**
```
adjusted_L_per_km = vehicle.litres_per_km * scenario.diesel_efficiency_improvement[year-1]
effective_price = max(0, DIESEL_PRICE - FUEL_TAX_CREDIT)  // $2.05 - $0.203 = $1.847
base_cost = adjusted_L_per_km * annual_kms * effective_price
fuel_cost[year] = base_cost * scenario.diesel_price_trajectory[year-1] * fuel_price_variation
```

**BEV:**
```
adjusted_kWh_per_km = vehicle.kwh_per_km
    * scenario.bev_efficiency_improvement[year-1]
    * charging_efficiency_variation

charging_mix = getDutyAdjustedChargingMix(vehicle, dutyCycle)
blended_rate = mix.retail * $0.30
             + mix.offpeak * $0.15
             + mix.solar * $0.04
             + mix.public * $0.50

base_cost = adjusted_kWh_per_km * annual_kms * blended_rate
electricity_cost = base_cost
    * scenario.electricity_price_trajectory[year-1]
    * electricity_price_variation

// Optional BEV road user charge (default off)
road_user_charge = 0
if apply_road_user_charge_bev:
    paired_diesel_L_per_km = paired_diesel.litres_per_km
        * scenario.diesel_efficiency_improvement[year-1]
    road_user_charge = annual_kms * max(0, paired_diesel_L_per_km * $0.305)

fuel_cost[year] = electricity_cost + road_user_charge
```

### 4.4 Maintenance Cost (per year, years 1-15)

```
base_rate = MAINTENANCE_COST_PER_KM[drivetrain][weight_class]
    BEV:    Light Rigid = $0.10,  Medium Rigid = $0.10,  Articulated = $0.19
    Diesel: Light Rigid = $0.18,  Medium Rigid = $0.18,  Articulated = $0.28

annual_base = annual_kms * base_rate
maintenance_cost[year] = annual_base
    * scenario.maintenance_cost_multiplier[year-1]
    * maintenance_cost_variation
```

The maintenance multiplier trajectory starts at 0.85 (year 1, new vehicle) and increases linearly to 1.25 (year 15, aging vehicle).

### 4.5 Battery Replacement (BEV only, year 8)

```
if drivetrain != BEV or year != 8: return 0

price_multiplier = scenario.battery_price_trajectory[7]  // year 8, index 7
cost_per_kWh = BATTERY_REPLACEMENT_COST * price_multiplier - BATTERY_RECYCLE_VALUE
             = $130 * multiplier - $13

replacement_cost = battery_capacity_kWh * cost_per_kWh

// Battery life variation adjusts cost (variation > 1.0 = longer life = lower cost)
if battery_life_variation:
    replacement_cost *= (2.0 - battery_life_variation)
```

At year 8 baseline: `$130 * 0.5596 - $13 = $59.75/kWh`

### 4.6 Carbon Cost (per year, years 1-15)

**Currently zero in all scenarios.** The logic exists but carbon_price_trajectory is all zeros.

**Diesel (if carbon price > 0):**
```
emissions_tonnes = (adjusted_L_per_km * annual_kms * 2.68) / 1000
carbon_cost[year] = emissions_tonnes * carbon_price_trajectory[year-1]
```

**BEV (if carbon price > 0):**
```
blended_emissions = mix.retail * 0.70 + mix.offpeak * 0.70
                  + mix.solar * 0.04 + mix.public * 0.70  (kg CO2e/kWh)
emissions_tonnes = (adjusted_kWh_per_km * annual_kms * blended_emissions) / 1000
carbon_cost[year] = emissions_tonnes * carbon_price_trajectory[year-1]
```

### 4.7 Charging Labour Cost (BEV only, constant per year)

```
if drivetrain != BEV: return 0

daily_kms = annual_kms / 255  (working days)
usable_range = vehicle.range_km * 0.6  (battery usable range factor)

sessions_per_day = 0                                       if daily_kms <= usable_range
                 = ceil((daily_kms - usable_range) / usable_range)  otherwise

hours_per_session = CHARGING_TIME_HOURS[weight_class]
    Light Rigid = 0.6h, Medium Rigid = 0.75h, Articulated = 1.0h

annual_charging_labour = sessions_per_day * hours_per_session * 255 * $47
```

### 4.8 Payload Penalty (constant per year)

```
if no comparison_pair: return 0

payload_difference = comparison_pair.payload - vehicle.payload
if payload_difference <= 0: return 0

freight_rate = FREIGHT_RATE_PER_TONNE_KM[weight_class]
    Light Rigid = $0.25,  Medium Rigid = $0.25,  Articulated = $0.08

utilisation = PAYLOAD_UTILISATION_FACTOR[weight_class]
    Light Rigid = 0.80,  Medium Rigid = 0.80,  Articulated = 0.90

annual_payload_penalty = payload_difference * freight_rate * annual_kms * utilisation
```

### 4.9 Residual Value (end of vehicle life)

```
residual = MSRP * (1 - 0.20)  // first year: 20% depreciation
for year 2..15:
    residual *= (1 - 0.10)    // ongoing: 10% per year

// i.e. residual = MSRP * 0.80 * 0.90^13

if BEV:
    residual *= scenario.bev_residual_value_multiplier[14]

if residual_value_variation:
    residual *= residual_value_variation

depreciation = MSRP - residual
```

### 4.10 Insurance (constant per year)

```
rate = 0.035 (BEV) or 0.0315 (Diesel)
annual_insurance = MSRP * rate + $2,000  (other insurance: permits, TAC, goods, PLI)
```

### 4.11 Registration (constant per year)

```
annual_registration = vehicle.annual_registration  (from catalog or override)
```

Light Rigid / Medium Rigid: $653/year. Articulated: $6,872/year.

---

## 5. NPV Methodology

### Discount Rate: 5% annual

### Convention: Annuity-Due

Year 1 cashflows are NOT discounted. Year n flows are discounted by `(1+r)^(n-1)`.

### What Gets Discounted and How

| Cost Component | Method | Detail |
|----------------|--------|--------|
| Fuel (15 annual cashflows, varying) | `calculateNpvOfAnnualCashflows` | `SUM[i=0..14]: cost[i] / (1.05)^i` |
| Maintenance (15 annual, varying) | `calculateNpvOfAnnualCashflows` | Same |
| Battery replacement (single, year 8) | `discountToPresent` | `cost / (1.05)^7` |
| Carbon (15 annual, varying) | `calculateNpvOfAnnualCashflows` | Same |
| Charging labour (15 annual, constant) | `calculateNpvOfAnnualCashflows` | Same |
| Payload penalty (15 annual, constant) | `calculateNpvOfAnnualCashflows` | Same |
| Insurance (level annuity) | `calculatePresentValue` | `annual * ((1-(1.05)^-15)/0.05) * 1.05` |
| Registration (level annuity) | `calculatePresentValue` | Same formula |
| Residual value (single, year 15) | `discountToPresent` | `residual / (1.05)^14` |
| Financing payments (60 monthly) | `calculateNpvOfPayments` | `SUM[m=1..60]: payment / (1.05)^(m/12)` |

### NOT Discounted (nominal figures in breakdown only)

| Field | Calculation |
|-------|-------------|
| `nominal_costs.insurance_cost` | `annual_insurance * 15` |
| `nominal_costs.registration_cost` | `annual_registration * 15` |
| `nominal_costs.financing_cost` | `total_payments - loan_amount` |
| `nominal_costs.depreciation` | `MSRP - residual_future_value` |

### Total Cost (Authoritative Comparison Metric)

```
total_cost = npv_purchase_payments
           + npv_fuel
           + npv_maintenance
           + npv_insurance      (PV annuity)
           + npv_registration   (PV annuity)
           + npv_battery_replacement
           + npv_carbon
           + npv_charging_labour
           + npv_payload_penalty
           - npv_residual_value

annual_cost = total_cost / ((1 - 1.05^-15) / 0.05 * 1.05)
cost_per_km = annual_cost / annual_kms
```

---

## 6. Output Structure

### `CalculationResponsePayload`

```typescript
{
  vehicle_id: string;
  scenario_name: ScenarioKey;
  total_cost: number;       // Authoritative NPV-adjusted total
  annual_cost: number;      // Annualised equivalent
  cost_per_km: number;      // annual_cost / annual_kms
  breakdown: {
    npv_costs: {
      fuel_cost, maintenance_cost, battery_replacement_cost,
      carbon_cost, charging_labour_cost, payload_penalty_cost,
      residual_value
    },
    nominal_costs: {
      insurance_cost, registration_cost, financing_cost, depreciation
    },
    upfront_costs: {
      purchase_cost, taxes_and_fees
    }
  }
}
```

---

## 7. Input Parameters

### Core Request

| Field | Type | Required | Options |
|-------|------|----------|---------|
| `vehicle_id` | string | Yes | BEV001-BEV008, DSL001-DSL008 |
| `scenario_name` | ScenarioKey | Yes | `baseline`, `technology_breakthrough`, `oil_crisis` |
| `purchase_method` | PurchaseMethod | Yes | `financed`, `outright` |
| `duty_cycle` | DutyCycle | No | `{ urban, regional, longHaul }` summing to ~100 |

### Cost Overrides (sensitivity adjustments)

| Override | Type | Default | Range | Effect |
|----------|------|---------|-------|--------|
| `annual_kms_variation` | absolute | vehicle default | 5,000-250,000 | Replaces annual kms |
| `residual_value_variation` | multiplier | 1.0 | 0.5-1.5 | Scales residual value |
| `fuel_price_variation` | multiplier | 1.0 | 0.5-2.0 | Scales diesel price trajectory |
| `electricity_price_variation` | multiplier | 1.0 | 0.5-2.0 | Scales electricity price trajectory |
| `maintenance_cost_variation` | multiplier | 1.0 | 0.5-1.5 | Scales maintenance cost |
| `battery_life_variation` | value | 1.0 | 0.5-1.5 | Affects replacement cost via `(2.0 - variation)` |
| `charging_efficiency_variation` | multiplier | 1.0 | 0.7-1.3 | Scales kWh/km |
| `apply_road_user_charge_bev` | boolean | false | -- | Toggles BEV road user charge |

### Vehicle Parameter Overrides (spec adjustments per vehicle)

| Override | Range | Replaces |
|----------|-------|----------|
| `msrp_override` | $0-$10M | Vehicle MSRP |
| `payload_override` | 0-100t | Vehicle payload |
| `range_km_override` | 50-2,500 km | Vehicle range |
| `battery_capacity_kwh_override` | 0-2,000 kWh | Battery size |
| `kwh_per_km_override` | 0.1-10 | Energy consumption |
| `litres_per_km_override` | 0.05-5 | Fuel consumption |
| `annual_registration_override` | $0-$100K | Registration cost |
| `interest_rate_override` | 0-0.20 | Loan interest rate |
| `charging_time_hours_override` | 0.1-8h | Hours per charge session |

---

## 8. Scenario System

Three scenarios provide 15-year trajectory arrays (one multiplier per year). Each cost function multiplies its base calculation by the relevant trajectory value for that year.

### Trajectory Comparison Table

| Parameter | Baseline | Technology Breakthrough | Oil Crisis |
|-----------|----------|------------------------|------------|
| Diesel price growth | ~3%/yr compound | Same as baseline | Spike to 1.55x in yr 3, then ~3%/yr to 2.22x |
| Electricity price growth | ~2%/yr | Same as baseline | ~3%/yr |
| Battery cost decline | ~7%/yr (to 0.34x) | ~15%/yr (to 0.11x) | Same as baseline |
| BEV efficiency gain | ~2%/yr | ~4%/yr (double) | Same as baseline |
| Diesel efficiency gain | ~1%/yr | Same as baseline | ~2%/yr (double) |
| Maintenance multiplier | 0.85 to 1.25 (linear) | Same as baseline | Same as baseline |
| BEV residual value boost | 1.0x (none) | Up to 1.3x from yr 8 | None |
| Carbon price | $0 (all years) | $0 (all years) | $0 (all years) |
| Policy phase-out year | null | null | null |
| BEV road charge start | null | null | null |

### Carbon Price Rationale

Australia has no economy-wide carbon price. The Safeguard Mechanism applies only to facilities emitting >100,000 tCO2e/year, which doesn't directly impact individual vehicle TCO. All scenarios set carbon price to $0 with the framework ready for future policy changes.

---

## 9. Policy System

Six policy types exist, all disabled by default. They provide a framework for modelling government interventions.

| Policy | Type | How It Works |
|--------|------|--------------|
| Fixed Purchase Rebate | BEV only | Subtracts fixed dollar amount from initial cost |
| Percentage Purchase Rebate | BEV only | Subtracts percentage of MSRP (with optional cap) |
| Stamp Duty Exemption | BEV only | Reduces stamp duty by exemption percentage |
| Green Loan Subsidy | BEV only | Reduces interest rate for financing |
| Carbon Pricing | Diesel penalty | Annual charge = emissions_tonnes * price_per_tonne |
| Charging Infrastructure Grant | BEV only | Grant percentage of infrastructure cost (with cap) |

**Preset scenarios:**
- **Standard Incentives:** $20K rebate, 100% stamp duty exemption, 2pp interest rate reduction
- **Aggressive Incentives:** 15% rebate (capped $50K), 100% stamp duty exemption, 3pp rate reduction, 50% infrastructure grant (capped $500K), $50/tonne carbon price

---

## 10. Duty Cycle and Charging Mix

The duty cycle determines the BEV charging mix, which in turn determines electricity cost and emissions.

### Route-Type Charging Profiles

| Route Type | Off-peak Depot | Public DC Fast |
|------------|---------------|----------------|
| Urban | 90% | 10% |
| Regional | 75% | 25% |
| Long Haul | 35% | 65% |

### Default Duty Cycle: Urban 60%, Regional 25%, Long Haul 15%

This produces these base charging mixes:

| Weight Class | Off-peak | Public |
|--------------|----------|--------|
| Light Rigid | 86% | 14% |
| Medium Rigid | 86% | 14% |
| Articulated | 43% | 57% |

### Charging Prices

| Type | Price ($/kWh) | Emissions (kg CO2e/kWh) |
|------|---------------|------------------------|
| Retail | $0.30 | 0.70 |
| Off-peak depot | $0.15 | 0.70 |
| Solar | $0.04 | 0.04 |
| Public DC fast | $0.50 | 0.70 |

When the user adjusts the duty cycle, the charging mix is recalculated as a weighted average, then re-normalised.

---

## 11. Vehicle Catalog

### 8 BEV/Diesel Comparison Pairs

| BEV | Diesel | Weight Class | BEV Payload | DSL Payload | BEV MSRP | DSL MSRP | Annual kms |
|-----|--------|-------------|-------------|-------------|----------|----------|-----------|
| BEV001 Jac N75 | DSL001 Hino 300 | Light Rigid | 4.0t | 4.5t | $176,500 | $80,000 | 23,000 |
| BEV002 Hyundai Mighty E | DSL002 Hyundai Mighty | Light Rigid | 4.0t | 4.0t | $150,000 | $75,000 | 23,000 |
| BEV003 Jac N90 | DSL003 Hino 500 | Light Rigid | 5.0t | 6.0t | $150,000 | $130,000 | 23,000 |
| BEV004 Volvo FL | DSL004 Volvo FE | Medium Rigid | 10.5t | 12.0t | $200,000 | $220,000 | 23,000 |
| BEV005 MB eActros 300 | DSL005 MB Actros | Medium Rigid | 22.0t | 25.0t | $400,000 | $270,000 | 23,000 |
| BEV006 MB eActros 600 | DSL006 MB Actros | Articulated | 42.0t | 50.0t | $600,000 | $270,000 | 84,000 |
| BEV007 Volvo FH | DSL007 Volvo FH | Articulated | 42.0t | 50.0t | $450,000 | $280,000 | 84,000 |
| BEV008 Scania 45R | DSL008 Scania R560 | Articulated | 42.0t | 50.0t | $320,000 | $300,000 | 84,000 |

---

## 12. BEV vs Diesel: Structural Calculation Differences

| Feature | BEV | Diesel |
|---------|-----|--------|
| Fuel cost | kWh/km * blended electricity rate | L/km * (diesel_price - fuel_tax_credit) |
| Battery replacement | Year 8 replacement | Always $0 |
| Charging labour | Driver wait time at chargers | Always $0 |
| Carbon cost | Grid emissions per kWh | Diesel emissions per litre (2.68 kg/L) |
| Payload penalty | Typically penalised (lower payload than diesel) | Typically $0 (higher payload) |
| Insurance rate | 3.5% of MSRP | 3.15% of MSRP |
| Road user charge | Optional toggle (exempt by default) | Implicitly in diesel price (fuel excise) |
| Policies/rebates | Purchase rebates, stamp duty exemption, green loan | No special policies |
| Residual value | May get scenario multiplier | No multiplier |

---

## 13. Frontend Data Flow

```
Step 0: Select diesel truck
  -> updateWizard({ currentVehicle })
  -> filters BEVs to same weight class

Step 1: Select BEV(s) to compare
  -> updateWizard({ comparisonVehicles })

Step 2: Adjust parameters, view results
  -> React Hook Form watch (150ms debounce) -> syncToStore
  -> buildComparisonPayload(wizardData)
  -> 600ms debounce -> runComparison(payload)
  -> calculateComparison() [client-side, shared/calculator]
  -> CalculationResponsePayload[] -> setResults() -> re-render charts

Backend (parallel, non-blocking):
  -> useWizardAutosave: persists wizardData to POST/PUT /sessions
  -> useCalculationRunner: persists results to PUT /sessions after calc
```

### Deduplication and Ordering

- Payload hash prevents duplicate calculations for identical inputs
- Monotonic `requestId` prevents stale results from overwriting newer ones
- Results are reordered to match the vehicle order when the request was issued

---

## 14. Verification and Parity Testing

101 test fixtures in `verification_data.json`, generated by the Python reference implementation:

- **96 base cases:** 16 vehicles x 3 scenarios x 2 purchase methods
- **5 override cases:** Various combinations of cost and vehicle overrides

Tolerances:
- Dollar amounts: within $0.05 (1 decimal place)
- Cost per km: within $0.0005 (3 decimal places)

Test runner: `frontend/src/test/verification.test.ts` using Vitest.

---

## 15. Backend Role

The backend is a **persistence and analytics layer**, not a computation layer.

| Function | Detail |
|----------|--------|
| Session persistence | POST/PUT /sessions with wizard data and pre-computed results |
| Session retrieval | GET /sessions with Redis cache (30min TTL), fallback to PostgreSQL |
| Input validation | Pydantic models enforce ranges matching `OVERRIDE_LIMITS` |
| Analytics aggregation | BEV win rate, average payback, average cost delta, top vehicles |
| Access control | Per-session secrets (cookie-based, SHA-256 hashed), API key for analytics |
| Rate limiting | Sessions: 30/min, Analytics: 10/min, Vehicles: 60/min |
