# Total Cost of Ownership Analysis: Light and Medium Rigid Vehicles (2024-2035)
## Baseline Scenario Report

**Analysis Period:** 2024-2035 (15-year vehicle life)  
**Scenario:** Baseline - Current trajectory with moderate price increases  
**Date Generated:** 1 June 2024  

---

## Executive Summary

This analysis calculates Total Cost of Ownership (TCO) for all light and medium rigid vehicles over a 15-year period under the baseline economic scenario. The analysis covers **10 vehicles**: 5 Battery Electric Vehicles (BEVs) and 5 diesel vehicles across light rigid and medium rigid weight classes.

### Key Findings

**BEVs are significantly more cost-effective than diesel equivalents:**
- BEVs show 37-42% lower TCO compared to diesel counterparts
- Cost per kilometre ranges from $0.47-$0.98 for BEVs vs $0.80-$1.17 for diesel
- Annual costs range from $10,790-$22,624 for BEVs vs $18,448-$26,989 for diesel

---

## Vehicle TCO Results (Net Present Value, AUD)

### Light Rigid Vehicles

| Vehicle | Model | Type | Total TCO | Annual Cost | Cost/km |
|---------|-------|------|-----------|-------------|---------|
| BEV002 | Hyundai Mighty Electric | BEV | $161,845 | $10,790 | $0.47 |
| BEV003 | Jac N90 | BEV | $167,185 | $11,146 | $0.48 |
| BEV001 | Jac N75 | BEV | $177,201 | $11,813 | $0.51 |
| DSL002 | Hyundai Mighty | Diesel | $276,716 | $18,448 | $0.80 |
| DSL001 | Hino 300 | Diesel | $279,405 | $18,627 | $0.81 |
| DSL003 | Hino 500 | Diesel | $306,300 | $20,420 | $0.89 |

### Medium Rigid Vehicles

| Vehicle | Model | Type | Total TCO | Annual Cost | Cost/km |
|---------|-------|------|-----------|-------------|---------|
| BEV004 | Volvo FL | BEV | $221,178 | $14,745 | $0.64 |
| BEV005 | MB eActros 300 | BEV | $339,360 | $22,624 | $0.98 |
| DSL004 | Volvo FE | Diesel | $377,943 | $25,196 | $1.10 |
| DSL005 | MB Actros | Diesel | $404,838 | $26,989 | $1.17 |

---

## Baseline Scenario Parameters

### Economic Trajectories (2024-2038)

**Energy Price Increases:**
- Diesel: 3% annual increase (from $2.05/L to $3.10/L by 2038)
- Electricity: 2% annual increase (from base rates)

**Technology Improvements:**
- BEV efficiency: 2% annual improvement
- Diesel efficiency: 1% annual improvement
- Battery costs: 7% annual decrease (driving down replacement costs)

**Financial Parameters:**
- Discount rate: 5%
- Financing interest rate: 6%
- Vehicle life: 15 years
- Down payment: 20% of purchase price

---

## Key Variables and Inputs Applied

### Vehicle Operating Parameters
- **Annual kilometres:** 23,000 km (rigid vehicles)
- **Battery degradation:** 2.5% per year
- **Maintenance cost escalation:** 85% to 125% of base rate over vehicle life

### Energy Costs and Mix
- **Electricity charging:** 100% off-peak at $0.15/kWh
- **Diesel price:** $2.05/L base (includes fuel tax credit of $0.203/L)
- **Road user charge:** $0.305/L (included in diesel price)

### Financial Structure
- **Insurance rates:** 3.5% of value (BEV), 3.15% (diesel)
- **Depreciation:** 20% first year, 10% ongoing
- **Financing term:** 5 years at 6% interest

### Emissions Factors
- **Grid electricity:** 0.7 kgCO2e/kWh
- **Diesel:** 2.68 kgCO2e/L

---

## Policy Settings (Baseline Scenario)

**Current Status:** All policy incentives are **DISABLED** in the baseline scenario

Available but inactive policies include:
- Fixed purchase rebates
- Percentage-based purchase rebates
- Stamp duty exemptions for BEVs
- Carbon pricing on diesel emissions
- Green loan subsidies (reduced interest rates)
- Charging infrastructure grants

---

## Cost Component Breakdown

### Typical Light Rigid BEV (Hyundai Mighty Electric - BEV002)
- **Purchase cost:** $30,900 (down payment)
- **Financing cost:** $19,772
- **Fuel cost:** $18,004 (15-year NPV)
- **Maintenance cost:** $25,674 (15-year NPV)
- **Insurance cost:** $108,750 (15-year total)
- **Registration:** $9,795 (15-year total)
- **Battery replacement:** $4,496 (NPV)
- **Less depreciation:** $126,224

### Typical Light Rigid Diesel (Hyundai Mighty - DSL002)
- **Purchase cost:** $15,450 (down payment)
- **Financing cost:** $12,375
- **Fuel cost:** $156,364 (15-year NPV, major cost driver)
- **Maintenance cost:** $88,560 (higher than BEV)
- **Insurance cost:** $93,937 (15-year total)
- **Registration:** $9,795 (15-year total)
- **Less depreciation:** $63,224

---

## Year-by-Year Analysis Available

The complete analysis includes detailed year-by-year cost breakdowns (2024-2038) for each vehicle, showing:
- Annual fuel costs (with price escalation)
- Maintenance costs (with degradation factors)
- Battery replacement timing and costs
- Depreciation schedules
- Carbon costs (if applicable)

---

## Data Sources and Methodology

**Vehicle Specifications:** Based on current market data for available models  
**Energy Prices:** Australian retail rates with projected increases  
**Financial Parameters:** Commercial truck financing rates  
**Maintenance Costs:** Industry benchmarks by weight class and drivetrain  
**Emissions Factors:** Australian grid mix and fuel standards  

**Calculation Method:** Net Present Value using 5% discount rate over 15-year vehicle life

---

## Files Generated

1. **Complete Dataset:** `tco_analysis_baseline_20250601_130119.json`
   - Full year-by-year breakdowns for all vehicles
   - Complete scenario and policy parameters
   - All input variables and constants

2. **Summary Report:** This document

The JSON file contains the complete dataset with all variables, inputs, policies, and scenario parameters used in the calculations, providing full transparency and traceability of the analysis. 