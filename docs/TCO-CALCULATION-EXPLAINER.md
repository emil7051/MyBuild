# How the TCO Calculator Works: A Plain-Language Guide

## What It Does

This tool compares the total cost of owning a battery-electric truck (BEV) against a diesel truck over 15 years. It accounts for everything from the purchase price to fuel, maintenance, battery replacement, driver time at chargers, lost payload capacity, and the truck's resale value at end of life.

All costs are converted to today's dollars using a 5% discount rate, so a dollar spent in year 10 counts less than a dollar spent today. The final number ("total cost of ownership") is what you'd need in the bank today to cover all costs for 15 years of operation.

---

## The Core Calculation

For each truck, the calculator runs through this sequence:

### 1. Purchase and Financing

The truck costs its sticker price (MSRP) plus 3% stamp duty, minus any BEV rebates.

If financed (the default): 20% down, 5-year loan at 6% interest. The calculator computes the net present value of all 60 monthly payments plus the down payment.

If bought outright: the full price is an immediate cost.

### 2. Fuel or Energy (varies each year)

**Diesel trucks:** litres per km multiplied by the effective diesel price ($2.05/L minus the $0.203/L fuel tax credit = $1.847/L), multiplied by annual kilometres. The diesel price grows over time per the selected scenario.

**Electric trucks:** kWh per km multiplied by a blended electricity rate. The rate depends on the charging mix (how much depot charging vs public fast charging the truck uses), which in turn depends on the duty cycle (proportion of urban, regional, and long-haul driving).

Typical blended rates:
- Light/medium rigid (mostly depot charging): ~$0.20/kWh
- Articulated (more public fast charging): ~$0.35/kWh

Both fuel types have efficiency improvements built in. BEVs get 2% better each year (baseline). Diesel gets 1%.

### 3. Maintenance (varies each year)

A per-kilometre rate multiplied by annual kms. BEVs are cheaper to maintain (fewer moving parts).

| | Light/Medium Rigid | Articulated |
|---|---|---|
| BEV | $0.10/km | $0.19/km |
| Diesel | $0.18/km | $0.28/km |

Maintenance increases with vehicle age: starting at 85% of the base rate in year 1, rising linearly to 125% by year 15.

### 4. Battery Replacement (BEV only, year 8)

Electric trucks get a mid-life battery replacement in year 8. The cost depends on battery size and how far battery prices have fallen by then.

Formula: `battery_kWh * ($130/kWh * price_trajectory - $13 recycling credit)`

In the baseline scenario, battery prices have dropped to ~56% of today's levels by year 8, so the effective cost is about $60/kWh.

### 5. Insurance (constant each year)

3.5% of MSRP for BEVs, 3.15% for diesel, plus $2,000/year for other insurance (permits, goods insurance, etc.).

### 6. Registration (constant each year)

From the vehicle catalog. Light/medium rigid: $653/year. Articulated: $6,872/year.

### 7. Charging Labour (BEV only)

If the truck's daily route exceeds its usable range (60% of rated range, accounting for reserve), a driver has to wait at a charger. The cost is the number of charging sessions multiplied by the session duration and driver's wage ($47/hour).

For a truck that doesn't need to charge mid-route, this cost is zero.

### 8. Payload Penalty

If the BEV carries less freight than its diesel equivalent (common because batteries are heavy), the operator loses revenue. The penalty uses industry freight rates per tonne-km and a utilisation factor.

Example: a BEV with 8 tonnes less payload than its diesel pair, running 84,000 km/year on articulated freight rates ($0.08/t-km, 90% utilisation) = ~$48,384/year.

### 9. Residual Value (end of year 15)

The truck's resale value, calculated as MSRP depreciated 20% in year 1 and 10% each year after. This is discounted back to today's dollars and subtracted from total cost.

### 10. Carbon Cost

A framework exists but is currently set to zero in all scenarios. Australia doesn't have an economy-wide carbon price, and the Safeguard Mechanism doesn't apply to individual vehicles.

---

## How Costs Are Grouped in the Output

| Group | What's in it | Treatment |
|-------|-------------|-----------|
| **NPV costs** | Fuel, maintenance, battery replacement, carbon, charging labour, payload penalty, residual value | Discounted to present value |
| **Nominal costs** | Insurance, registration, financing interest, depreciation | Simple multiplication (shown for transparency, not used in the comparison metric) |
| **Upfront costs** | Down payment or purchase price, stamp duty | Immediate cash outlay |

The **total_cost** (the comparison metric) uses NPV for everything. The nominal costs in the breakdown are informational only.

---

## What Users Can Change

### Scenario (changes trajectory assumptions)

| Scenario | Story | Key differences |
|----------|-------|-----------------|
| **Baseline** | Current trends continue | Diesel +3%/yr, electricity +2%/yr, battery costs -7%/yr |
| **Technology Breakthrough** | Rapid EV improvement | Battery costs drop to 11% of today's, BEV efficiency doubles improvement rate, resale values increase |
| **Oil Crisis** | Fuel supply disruption | Diesel price spikes 55% in year 3 then keeps rising, electricity also rises faster |

### Operating Parameters

| Parameter | What it does | Default |
|-----------|-------------|---------|
| Purchase method | Financed (20% down, 5yr loan) or outright | Financed |
| Duty cycle | Urban/regional/long-haul split | 60/25/15 |
| Annual kilometres | Total kms per year | 23,000 (rigid) or 84,000 (articulated) |
| Diesel price variation | Scale diesel prices up or down | 1.0x (no change) |
| Electricity price variation | Scale electricity prices up or down | 1.0x |
| Maintenance cost variation | Scale maintenance up or down | 1.0x |
| Battery life variation | Longer battery life reduces replacement cost | 1.0x |
| Charging efficiency variation | More/less energy per km | 1.0x |
| Residual value variation | Better/worse resale | 1.0x |
| BEV road user charge | Whether BEVs pay road user charges | Off |

### Per-Vehicle Overrides

Users can also override individual vehicle specs: MSRP, payload, range, battery size, energy/fuel consumption, registration cost, interest rate, and charging time.

---

## Where the Data Comes From

### Cited Sources

| Data | Source |
|------|--------|
| Diesel price ($2.05/L) | Australian Institute of Petroleum (AIP) average retail, +2c/L for AdBlue |
| Annual kms (23,000 rigid, 84,000 articulated) | ABS Survey of Motor Vehicle Use (SMVU) |
| Charging mix proportions | SMVU trip data + Scania eMobility Hub charging strategies |
| Articulated public charging share (57%) | ARENA/AECOM industry consultation |
| Diesel insurance rate (3.15%) | Transport Industry Council guidelines |
| Interest rate (6%) | Savvy (commercial truck financing) |
| Stamp duty (3%) | freightmetrics.com.au |
| Freight rates per tonne-km | BITRE 2017 (Bureau of Infrastructure and Transport Research Economics) |
| Charger cost ($300K) | Smart Freight Media Centre |
| Driver wage ($47/hr) | Award wage Grade 8 with overtime (49hr week), super, leave loading, workers comp |
| Carbon pricing rationale | Australian Government Safeguard Mechanism, DCCEEW, IEA, Climate Change Authority |

### Values Without Specific Citations

| Data | Value | Notes |
|------|-------|-------|
| Electricity prices | $0.15-$0.50/kWh range | Industry estimates, not specifically cited |
| Maintenance $/km | BEV $0.10-$0.19, Diesel $0.18-$0.28 | Flagged in code as "check with T&E" |
| Battery replacement cost | $130/kWh | Industry consensus pricing |
| Battery recycling credit | $13/kWh | Estimate |
| Depreciation rates | 20% year 1, 10% ongoing | Standard commercial vehicle depreciation |
| Discount rate (5%) | Standard corporate discount rate | Not specific to any industry source |
| Grid emissions (0.70 kg CO2e/kWh) | Australian NEM average | Not specifically cited |
| Diesel emissions (2.68 kg CO2e/L) | Standard figure | Not specifically cited |
| BEV insurance premium (3.5%) | Higher than diesel due to newer technology | Not specifically cited |

### Vehicle Specifications

Vehicle data (MSRP, payload, range, battery capacity, energy consumption) comes from manufacturer specifications for current Australian-market models. The Python file `data/vehicles.py` is the authoritative source, with `data/vehicle_models.csv` being a legacy reference (note: the CSV has some values that differ from the Python file; the Python file is definitive).

---

## Extensions and What Can Be Varied

### Already Built (Toggle or Configure)

1. **Policy incentives** (six types, all disabled by default): purchase rebates (fixed or percentage), stamp duty exemption, green loan interest subsidy, carbon pricing, charging infrastructure grants. Preset scenarios: "Standard Incentives" and "Aggressive Incentives"

2. **Road user charges for BEVs** (toggle in cost overrides). Uses the paired diesel's fuel consumption to calculate an equivalent charge at $0.305/litre

3. **Duty cycle sensitivity**: shifting the urban/regional/long-haul split changes the charging mix, which changes electricity cost and charging labour

### Built Into the Framework (Currently Set to Zero)

4. **Carbon pricing trajectories**: the calculation logic fully handles annual carbon charges. Enabling requires non-zero values in `scenario.carbon_price_trajectory`

5. **Policy phase-out year**: scenarios can specify a year when BEV incentives expire (currently null in all scenarios)

6. **BEV road user charge start year**: scenarios can specify when BEVs begin paying road charges (currently null)

### Possible Without Code Changes (Data Layer Only)

7. **New vehicle models**: add entries to `data/vehicles.py`, run the generation script. No calculator changes needed

8. **New scenarios**: add to `data/scenarios.py` with different trajectory arrays. The calculator picks up new scenarios automatically

9. **Updated constants**: change prices, rates, or maintenance costs in `data/constants.py` and regenerate. Immediate effect

10. **New policy presets**: combine the six policy types in `data/policies.py` to model different government packages

### Would Require Code Changes

11. **New cost components**: adding a cost category (e.g. tyre wear, tolls, driver training) requires changes to `tcoCalculator.ts` and the `CostBreakdown` type

12. **Non-linear trajectories**: the current system uses simple multiplier arrays. More complex models (e.g. stochastic fuel prices, correlated variables) would need new trajectory logic

13. **Multi-vehicle fleet modelling**: the calculator handles one vehicle at a time. Fleet-level optimisation (mix of vehicles, shared infrastructure) is out of scope

14. **Infrastructure cost integration**: charger and grid upgrade constants exist in the data layer (`$300K charger, $1M grid upgrade`) but are not wired into the TCO calculation. They could be added as an upfront or amortised cost component

15. **Solar/storage integration**: solar panel and battery storage installation constants exist but aren't used in calculations. Could be modelled as reducing the blended electricity rate

---

## Verification

The TypeScript calculator is verified against a Python reference implementation via 101 test cases. Every vehicle, scenario, and purchase method combination is tested, plus 5 additional cases with overrides applied.

Tolerances: dollar amounts match within 5 cents, cost per km within 0.05 cents.

This means you can trust that the TypeScript engine (which runs in the browser) produces the same results as the Python reference that was used to validate the methodology.
