# **TCO Calculator \- Technical Specification**

The TCO Calculator is a quantitative modeling tool designed to assess and compare the total cost of ownership (TCO) and associated emissions for battery-electric trucks (BETs) versus conventional diesel trucks. It supports fleet operators, policymakers, and researchers by providing cost analysis under various economic scenarios and policy settings.

## **1\. System Architecture**

### **1.1 Component Overview**

| Layer | Purpose | Key Components |
| :---- | :---- | :---- |
| Data Core | Static data, policies & scenarios  | Vehicle specifications, economic scenarios, policy definitions, global constants |
| Calculation Engine | Finance and operations modelling | Vehicle calcs, financial calcs, operating calcs, financial utilities \-\> TCO Calculation |
| Analysis Suite | Analytical capabilities | Monte Carlo simulation, sensitivity analysis |
| Output Layer | Structured results | TCOResult objects, simulations, and outputs |

├── calculations/  
    ├── calculations.py    \# TCO aggregation, TCOResult  
    ├── financial.py       \# Purchase, financing, depreciation  
    ├── inputs.py          \# VehicleInputs, VehicleData  
    ├── operating.py       \# Fuel, battery, maintenance costs etc  
    ├── simulation.py      \# Analysis (Monte Carlo, Sensitivity)  
    └── utils.py           \# Financial utilities (PV, NPV, etc)  
├── data/  
     ├── constants.py       \# Global constants  
     ├── policies.py        \# Policy dataclasses and logic  
     ├── scenarios.py       \# EconomicScenario definitions  
     └── vehicles.py        \# VehicleModel definitions

### **1.2 Key Components & Data Flow**

* **Data Core (data/ directory):** Central repository for all input data.  
  * **vehicles.py**: An imported database of vehicle models with static attributes like MSRP, range, battery capacity, efficiency. Defines VehicleModel and manages the dictionary of vehicle models (ALL\_MODELS, BY\_ID).  
  * **scenarios.py**: Defines EconomicScenario (time-varying parameters like fuel/electricity prices, battery degradation, efficiency improvements) and manages predefined scenarios (SCENARIOS). Scenarios can be created, or specific variable parameters modified here.   
  * **policies.py**: Defines PolicyIncentive base class and specific policy dataclasses (e.g., PurchaseRebate, StampDutyExemption, CarbonPrice). Manages a POLICIES dictionary and functions to calculate policy impacts prior to TCO calculation.  
  * **constants.py**: Centralised list of global constants (e.g., default prices, tax rates, vehicle life, discount rates).

* **Calculation Engine (calculations/ directory):** Contains all financial and operational cost computation logic. The four files inputs / financial / operating and utils are all pre-calculation logic to make the final TCO calculation in [calculations.py](http://calculations.py) as simple and transparent as possible.

  * **inputs.py**:  
    * Defines VehicleInputs: The most critical dataclass that aggregates data from VehicleModel, EconomicScenario, and purchase\_method ('outright' or 'financed'). It pre-calculates many sub-components for TCO analysis (net purchase cost, financing details, base annual operating costs).  
    * Defines VehicleData: Acts as an access point and cache for VehicleInputs objects, improving performance.

  * **financial.py**:  
    * Standalone functions for financial calculations (e.g., calculate\_stamp\_duty, calculate\_rebate, calculate\_initial\_cost), incorporating policy impacts.  
    * FinancingCalculator: Class for loan-based financing (down payment, loan principal, interest rates, monthly payments, total financing costs).  
    * DepreciationCalculator: Class for vehicle depreciation and residual value calculations, accommodating different rates and scenario-based BEV residual value adjustments.

  * **utils.py**: Common financial utility functions (e.g. calculate\_present\_value, discount\_to\_present, calculate\_npv\_of\_payments, calculate\_npv\_of\_annual\_cashflows).

  * **operating.py**:  
    * FuelCostCalculator: Determines annual fuel (diesel) or electricity (BEV) costs, factoring in efficiency, mileage, scenario-driven prices/efficiency improvements, and BEV charging mix.  
    * MaintenanceCostCalculator: Calculates annual maintenance based on vehicle type, mileage, drivetrain rates, and scenario-driven multipliers.  
    * InsuranceCostCalculator: Calculates annual insurance based on MSRP, drivetrain rates, and other fixed costs.  
    * BatteryReplacementCalculator: For BEVs, calculates battery replacement cost, considering capacity, scenario-adjusted cost/kWh, and recycle value.  
    * PayloadPenaltyCalculator: Calculates annual cost penalty for reduced payload capacity in BEVs compared to equivalent diesel vehicles, based on freight rates per tonne-kilometre.
    * calculate\_carbon\_cost\_year: For diesel, calculates annual carbon emission costs based on consumption, CO2 factor, and scenario-driven carbon prices.  

  * **calculations.py**:  
    * Defines TCOResult: Standardised dataclass for TCO calculation output (total cost, annual cost, cost/km, component breakdowns including payload penalty cost). If we want additional reporting the first thing to do would be to adjust the expected output here.   
    * calculate\_tco\_from\_inputs(vehicle\_inputs: VehicleInputs, overrides: Optional[Dict[str, float]] = None) -> TCOResult: Core function that aggregates all discounted costs and revenues from a VehicleInputs object to determine TCO, average annual cost, and cost/km. The optional `overrides` parameter allows for variation of specific parameters during Monte Carlo simulation or sensitivity analysis without modifying the base VehicleInputs object.
    * Primary API functions: calculate\_tco, calculate\_all\_tcos, compare\_vehicle\_pairs, calculate\_scenario\_comparison, calculate\_breakeven\_analysis. These provide a clean, single-purpose interface for all TCO calculations.
    * Note: The module follows clean code principles with a streamlined API. All calculations flow through VehicleInputs objects, ensuring consistency and avoiding duplication.

* **Analysis Suite (calculations/simulation.py):**  
  * MonteCarloSimulation: Performs Monte Carlo simulations using an efficient "overrides dictionary" approach. Defines UncertaintyParameter (with override_key field) and SimulationResults. The simulation passes parameter overrides through the calculation chain without modifying objects, improving performance and maintainability.
  * SensitivityAnalysis: Performs deterministic sensitivity analysis by varying one input parameter at a time through the overrides mechanism to quantify its impact on TCO, useful for generating tornado diagrams.

* **Output Layer:**  
  * **TCOResult objects:** Detailed, structured output for individual TCO calculations, including payload penalty cost for vehicles with reduced cargo capacity. These can be reported or visualised in different ways.  
  * **SimulationResults objects:** Comprehensive output from Monte Carlo simulations, including statistical summaries.  
  * Data from **SensitivityAnalysis**: Typically lists of tuples suitable for graphing \- eg. tornado graphs. 

## **2\. Core Data Structures**

### **2.1 Vehicle Model**

The VehicleModel dataclass (**data.vehicles.VehicleModel**) contains all static attributes of a truck model (MSRP, range, efficiency, payload, battery capacity).

| Attribute | Type | Description |
| :---- | :---- | :---- |
| vehicle\_id | str | Unique identifier (e.g., 'BEV001', 'DSL001') |
| comparison\_pair | str | ID of comparable vehicle with different drivetrain |
| weight\_class | str | 'Light Rigid', 'Medium Rigid', or 'Articulated' |
| drivetrain\_type | str | 'BEV' or 'Diesel' |
| model\_name | str | Vehicle model designation |
| payload | float | Maximum payload capacity (tonnes) |
| msrp | float | Manufacturer's suggested retail price (AUD) |
| range\_km | float | Operational range per tank/charge |
| battery\_capacity\_kwh | float | Battery capacity for BEVs (0 for diesel) |
| kwh\_per\_km | float | Energy efficiency for BEVs |
| litres\_per\_km | float | Fuel efficiency for diesel vehicles |
| annual\_kms | float | Expected annual kilometres driven |
| annual\_registration | float | Annual registration cost (AUD) |

### **2.2 Policies**

The policy system uses inheritance with a base class **policies.PolicyIncentive** for  definitions. Subclasses like PurchaseRebate, StampDutyExemption, CarbonPrice define specific policy mechanisms.

| Policy Type | Key Parameters | Application |
| :---- | :---- | :---- |
| PurchaseRebate | Fixed amount ($) | Direct reduction in purchase price |
| PercentageRebate | Percentage of MSRP, optional cap | Percentage-based incentive |
| StampDutyExemption | Exemption percentage (0-1) | Reduction in stamp duty tax |
| CarbonPrice | Price per tonne CO2e | Annual charge on diesel emission |
| GreenLoanSubsidy | Interest rate reduction | Lower financing costs for BEVs |
| ChargingInfrastructureGrant | Grant percentage, optional cap | Infrastructure investment support |

* **inputs.VehicleInputs**: Aggregates VehicleModel, EconomicScenario, and purchase\_method. Pre-calculates net initial costs, financing details, baseline annual operating costs, and payload penalty (annual cost of reduced cargo capacity for BEVs).

* **calculations.TCOResult**: The comprehensive TCO breakdown for a single vehicle calculation (total TCO (NPV), ave. annual cost, cost/km, itemised components including residual value).

* **simulation.UncertaintyParameter**: Defines uncertain parameters for Monte Carlo simulation with probability distributions (normal, uniform, triangular) and an `override_key` field that maps to the specific parameter to vary in the calculation chain.

## **3\. TCO Calculation Flow (calculate\_tco\_from\_inputs)**

The TCO for a VehicleInputs object is calculated as follows:

**Function signature:** `calculate_tco_from_inputs(vehicle_inputs: VehicleInputs, overrides: Optional[Dict[str, float]] = None) -> TCOResult`

The optional `overrides` parameter allows for variation of specific parameters during Monte Carlo simulation or sensitivity analysis without modifying the base VehicleInputs object.

1. **Determine Purchase & Financing Cash Flows:**

   * **Outright Purchase:**   
     * upfront\_cost \= vehicle\_inputs.initial\_cost  
     * financing\_cost \= 0\.   
     * npv\_purchase\_payments \= initial\_cost.

   * **Financed Purchase:**   
     * upfront\_cost \= vehicle\_inputs.down\_payment.   
     * financing\_cost \= vehicle\_inputs.total\_financing\_cost (undiscounted sum for reporting).   
     * npv\_purchase\_payments \= down\_payment \+ NPV of all monthly loan payments (discounted month-by-month).

2. **Calculate Residual Value at End of Vehicle Life:**  
   * Retrieve the vehicle's residual value at year 15 using vehicle\_inputs.get\_residual\_value(const.VEHICLE\_LIFE).
   * Discount this future residual value to present value using const.DISCOUNT\_RATE.
   * This considers initial cost, depreciation rates, and scenario-specific BEV residual value adjustments.

3. **Calculate Net Present Value (NPV) of Annual Operating Costs:**

   * Generate lists of annual costs over the vehicle life:
     * Annual fuel/electricity costs for each year
     * Annual battery replacement costs (typically non-zero in one year for BEVs)
     * Annual carbon costs (diesel only)
     * Annual maintenance costs
     * Annual payload penalties (BEVs with less payload than comparison vehicle)

   * Calculate NPV of each cost category using calculate\_npv\_of\_annual\_cashflows utility function, which discounts each year's costs to present value and sums them.

4. **Calculate NPV of Fixed Annual Costs (Insurance & Registration):**

   * Calculate PV of total insurance costs (vehicle\_inputs.annual\_insurance\_cost as an annuity).

   * Calculate PV of total registration costs (vehicle\_inputs.vehicle.annual\_registration as an annuity).

5. **Calculate Total TCO:**

   	total\_cost \=   
   	npv\_purchase\_payments \+   
   	total\_fuel\_cost (NPV) \+   
   	total\_maintenance\_cost (NPV) \+   
   	total\_insurance\_pv \+   
   	total\_registration\_pv \+   
   	total\_battery\_cost (NPV) \+   
   	total\_carbon\_cost (NPV) \+   
   	total\_payload\_penalty (NPV) \-   
   	residual\_value\_pv (present value of residual value).

6. **Derive Aggregated Metrics:**

   * annual\_cost \= total\_cost / const.VEHICLE\_LIFE (simple average).

   * cost\_per\_km \= annual\_cost / vehicle\_inputs.vehicle.annual\_kms.

7. **Populate and Return TCOResult Object:**

   * Includes identifiers, primary TCO figures, and a detailed breakdown of cost components including payload penalty cost and residual value.

## **4\. Key Calculation Logic / Classes**

| Topic | Key Logic / Formula | Source Modules/Classes |
| :---- | :---- | :---- |
| **Initial Cost** | MSRP \+ stamp\_duty \- rebate | financial.calculate\_initial\_cost (uses data.policies) |
| **Stamp Duty** | msrp \* STAMP\_DUTY\_RATE \- *adjusted by StampDutyExemption policy* | financial.calculate\_stamp\_duty, data.policies |
| **Rebate** | PurchaseRebate (fixed) \+ PercentageRebate (capped) \- *only one will be non-zero* | financial.calculate\_rebate, data.policies |
| **Financing** | Numpy calculations for down payment, loan amount, monthly payment and interest \- *interest rate adjusted by GreenLoanSubsidy policy.* | financial.FinancingCalculator, data.policies |
| **Residual Value** | Calculated by applying annual depreciation rates to initial cost over vehicle life - *different rates for year 1 vs. ongoing* & *BEV residual value adjusted by EconomicScenario* | financial.DepreciationCalculator.get\_residual\_value |
| **Fuel/Electricity (Yr i)** | (base\_efficiency \* scenario\_efficiency\_multiplier) \* annual\_kms \* (base\_price \* scenario\_price\_multiplier) \- *for BEV models it also considers the charging mix from CHARGING\_MIX\_PROPORTIONS dictionary* | operating.FuelCostCalculator |
| **Maintenance (Yr i)** | (annual\_kms \* MAINTENANCE\_COST\_PER\_KM[drivetrain][weight\_class]) \* scenario\_maintenance\_multiplier  | operating.MaintenanceCostCalculator |
| **Battery Value (Yr y)** | battery\_capacity\_kwh \* (scenario\_adjusted\_cost\_per\_kWh \- recycle\_value) \- *typically in a single year.*  | operating.BatteryReplacementCalculator |
| **Carbon Cost (Yr i)** | (annual\_fuel\_consumption \* emissions\_factor) \* scenario\_carbon\_price | Operating.calculate\_carbon\_cost\_year |
| **Payload Penalty (Yr i)** | payload\_difference \* FREIGHT\_RATE\_PER\_TONNE\_KM[weight\_class] \* annual\_kms \* PAYLOAD\_UTILISATION\_FACTOR | operating.PayloadPenaltyCalculator |
| **NPV of Annual Cashflows** | Σ(cashflow\_i / (1 + discount\_rate)^i) for i = 1 to n | utils.calculate\_npv\_of\_annual\_cashflows |
| **Monte Carlo Overrides** | Parameters varied through overrides dictionary: fuel_price_variation, electricity_price_variation, maintenance_cost_variation, annual_kms_variation (absolute), residual_value_variation, battery_life_variation, charging_efficiency_variation | MonteCarloSimulation, all calculator classes accept overrides |


## **5\. Assumptions and Current Limitations**

* **Single Discount Rate:** A constant const.DISCOUNT\_RATE (currently 5% real) is used for all NPV calculations.

* **Residual Value Approach:** The TCO calculation uses the standard approach of subtracting the present value of the vehicle's residual value at end of life, rather than summing discounted depreciation charges.

* **Payload Penalty:** Implemented for BEVs with reduced payload capacity compared to diesel equivalents. Uses freight rates ($/tonne-km) and assumes 85% average payload utilisation. Only applies when comparison_pair is specified and BEV has less payload.

* **Monte Carlo Parameter Application:** The MonteCarloSimulation uses an efficient "overrides dictionary" approach, passing parameter variations through the calculation chain without object modification. Currently supports variations in: fuel/electricity prices, maintenance costs, annual kilometres (absolute value), residual value, battery life, and charging efficiency. The system is easily extensible for additional parameters.

* **Reliance on Input Data:** Accuracy depends heavily on constants in data/constants.py, vehicle data in data/vehicles.py, and scenario definitions in data/scenarios.py. These require regular review and updates.

* **Scenario Specificity:** TCO results are sensitive to the assumptions and trajectories defined in EconomicScenario object

### Appendix 1: Calculation Constants

**Financial Constants**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Real discount rate for NPV | DISCOUNT\_RATE | 0.05 | fraction (5%) | Standard commercial analysis |
| General inflation rate | INFLATION\_RATE | 0.025 | fraction (2.5%) | Australian economic projections |
| Base financing interest rate | INTEREST\_RATE | 0.06 | fraction (6%) | Commercial truck financing (Savvy) |
| Loan term duration | FINANCING\_TERM | 5 | years | Industry standard |
| Down payment percentage | DOWN\_PAYMENT\_RATE | 0.20 | fraction (20%) | Commercial lending standard |
| First year depreciation rate | DEPRECIATION\_RATE\_FIRST\_YEAR | 0.20 | fraction (20%) | Accounting standard |
| Ongoing annual depreciation rate | DEPRECIATION\_RATE\_ONGOING | 0.10 | fraction (10%) | Accounting standard |

**Electricity & Charging Infrastructure**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Retail workplace charging price | RETAIL\_CHARGING\_PRICE | 0.30 | $/kWh | Current market rates |
| Off-peak electricity price | OFFPEAK\_CHARGING\_PRICE | 0.15 | $/kWh | Current market rates |
| Solar electricity price | SOLAR\_CHARGING\_PRICE | 0.04 | $/kWh | Lifecycle cost estimate |
| Public fast charging price | PUBLIC\_CHARGING\_PRICE | 0.50 | $/kWh | Current market rates |
| Solar panel installation cost | SOLAR\_PANEL\_INSTALLATION | 1285 | $/kW DC | Industry estimates |
| Solar panel maintenance cost | SOLAR\_MAINTENANCE | 0.15 | $/kWh/year | Industry estimates |
| Battery storage installation cost | STORAGE\_INSTALLATION | 423 | $/kWh | Industry estimates |
| Battery storage maintenance rate | STORAGE\_MAINTENANCE | 0.025 | fraction (2.5%) | AEMO/NREL guidelines |
| Infrastructure lifespan | INFRASTRUCTURE\_LIFE | 15 | years | Industry standard |
| DC fast charger cost | CHARGER\_COST | 300000 | $ | Smart Freight Media Centre |
| Grid upgrade cost | GRID\_UPGRADE | 1000000 | $ | Industry estimates |

**Charging Mix** 

| Vehicle Type | Weight Class | Charging Type | Proportion | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| BEV | Light Rigid | Retail | 0.00 (0%) | SMVU & Scania eMobility Hub |
| BEV | Light Rigid | Off-peak | 0.86 (86%) | SMVU & Scania eMobility Hub |
| BEV | Light Rigid | Public | 0.14 (14%) | SMVU & Scania eMobility Hub |
| BEV | Light Rigid | Solar | 0.00 (0%) | No solar infrastructure assumed |
| BEV | Medium Rigid | Retail | 0.00 (0%) | SMVU & Scania eMobility Hub |
| BEV | Medium Rigid | Off-peak | 0.86 (86%) | SMVU & Scania eMobility Hub |
| BEV | Medium Rigid | Public | 0.14 (14%) | SMVU & Scania eMobility Hub |
| BEV | Medium Rigid | Solar | 0.00 (0%) | No solar infrastructure assumed |
| BEV | Articulated | Retail | 0.00 (0%) | SMVU & Scania eMobility Hub |
| BEV | Articulated | Off-peak | 0.67 (67%) | SMVU & Scania eMobility Hub |
| BEV | Articulated | Public | 0.33 (33%) | SMVU & Scania eMobility Hub |
| BEV | Articulated | Solar | 0.00 (0%) | No solar infrastructure assumed |

**Fuel Cost**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Diesel price including AdBlue | DIESEL\_PRICE | 2.05 | $/litre | Australian Institute of Petroleum |

**Labour Cost** 

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Driver hourly wage | HOURLY\_WAGE | 47 | $/hour | Award wage grade 8 (49hr week basis) |

**Emissions Factor** 

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Diesel emissions factor | DIESEL\_EMISSIONS | 2.68 | kg CO2e/litre | Australian emissions factors |
| Retail electricity emissions | RETAIL\_CHARGING\_EMISSIONS | 0.7 | kg CO2e/kWh | Australian grid data |
| Off-peak electricity emissions | OFFPEAK\_CHARGING\_EMISSIONS | 0.7 | kg CO2e/kWh | Australian grid data |
| Solar electricity emissions | SOLAR\_CHARGING\_EMISSIONS | 0.04 | kg CO2e/kWh | Lifecycle analysis |
| Public charging emissions | PUBLIC\_CHARGING\_EMISSIONS | 0.7 | kg CO2e/kWh | Australian grid data |

**Battery Parameters**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Battery replacement cost | BATTERY\_REPLACEMENT\_COST | 130 | $/kWh | Industry projections |
| Battery recycle value | BATTERY\_RECYCLE\_VALUE | 13 | $/kWh | Recycling market estimates |
| Battery degradation rate | BATTERY\_DEGRADATION\_RATE | 0.025 | fraction/year (2.5%) | Battery performance studies |

**Operating Parameters**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Vehicle operational lifespan | VEHICLE\_LIFE | 15 | years | Industry standard |
| Rigid truck annual distance | RIGID\_ANNUAL\_KMS | 23000 | km/year | SMVU (Survey of Motor Vehicle Use) |
| Articulated truck annual distance | ART\_ANNUAL\_KMS | 84000 | km/year | SMVU data |

**Operating Costs**

| Drivetrain | Weight Class | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- | :---- |
| All | All | BEV insurance rate | 0.035 | fraction (3.5%) | Industry estimates |
| All | All | Diesel insurance rate | 0.0315 | fraction (3.15%) | Transport Industry Council |
| All | All | Other insurance costs | 2000 | $/year | Industry estimates |
| BEV | Light Rigid | Maintenance rate | 0.10 | $/km | T\&E estimates (to be verified) |
| BEV | Medium Rigid | Maintenance rate | 0.10 | $/km | T\&E estimates (to be verified) |
| BEV | Articulated | Maintenance rate | 0.19 | $/km | T\&E estimates (to be verified) |
| Diesel | Light Rigid | Maintenance rate | 0.18 | $/km | T\&E estimates (to be verified) |
| Diesel | Medium Rigid | Maintenance rate | 0.18 | $/km | T\&E estimates (to be verified) |
| Diesel | Articulated | Maintenance rate | 0.28 | $/km | T\&E estimates (to be verified) |

**Government Policies & Incentives**

| Constant | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Fuel tax credit | FUEL\_TAX\_CREDIT | 0.203 | $/litre | Australian Tax Office |
| Road user charge | ROAD\_USER\_CHARGE | 0.305 | $/litre | Government policy |
| Stamp duty rate | STAMP\_DUTY\_RATE | 0.03 | fraction (3%) | freightmetrics.com.au |

**Payload Penalty**

| Weight Class | Parameter | Value | Unit | Data Source |
| :---- | :---- | :---- | :---- | :---- |
| Light Rigid | Freight rate | 0.17 | $/tonne-km | BITRE 2017 freight transport data |
| Medium Rigid | Freight rate | 0.17 | $/tonne-km | BITRE 2017 freight transport data |
| Articulated | Freight rate | 0.26 | $/tonne-km | BITRE 2017 freight transport data |
| All | Payload utilisation factor | 0.85 | fraction (85%) | Industry average - trucks rarely run at 100% capacity |

### Appendix 2: Vehicle Models & Static Attributes

**Battery Electric Vehicles (BEVs)**

| Model Name | Jac N75 | Hyundai ME | Jac N90 | Volvo FL | eActros 300 | eActros 600 | Volvo FH | Scania 45R |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Weight Class** | Light Rigid | Light Rigid | Light Rigid | Medium Rigid | Medium Rigid | Articulated | Articulated | Articulated |
| **Drivetrain Type** | BEV | BEV | BEV | BEV | BEV | BEV | BEV | BEV |
| **Payload Capacity (tonnes)** | 4.0 | 4.0 | 5.0 | 10.5 | 22.0 | 42.0 | 42.0 | 42.0 |
| **MSRP ($)** | 176,500 | 150,000 | 150,000 | 200,000 | 400,000 | 600,000 | 450,000 | 320,000 |
| **Range (km)** | 220 | 200 | 180 | 300 | 300 | 500 | 300 | 390 |
| **Battery Capacity (kWh)** | 100 | 97 | 107 | 264 | 336 | 621 | 540 | 624 |
| **Energy Efficiency (kWh/km)** | 0.48 | 0.48 | 0.61 | 1.09 | 1.09 | 1.2 | 1.2 | 1.2 |
| **Maintenance Cost ($/km)** | 0.05 | 0.05 | 0.05 | 0.08 | 0.08 | 0.12 | 0.12 | 0.12 |
| **Annual Registration ($/year)** | 653 | 653 | 653 | 653 | 653 | 6,872 | 6,872 | 6,872 |
| **Annual Distance (km/year)** | 23,000 | 23,000 | 23,000 | 23,000 | 23,000 | 84,000 | 84,000 | 84,000 |
| **Noise Pollution ($/km)** | 0.004 | 0.004 | 0.004 | 0.006 | 0.006 | 0.009 | 0.009 | 0.009 |

**Diesel Vehicles (DSL)**

| Model Name | Hino 300 | Hyundai M | Hino 500 | Volvo FE | MB Actros | MB Actros | Volvo FH | Scania R560 |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Weight Class** | Light Rigid | Light Rigid | Light Rigid | Medium Rigid | Medium Rigid | Articulated | Articulated | Articulated |
| **Drivetrain Type** | Diesel | Diesel | Diesel | Diesel | Diesel | Diesel | Diesel | Diesel |
| **Payload Capacity (tonnes)** | 4.5 | 4.0 | 6.0 | 12.0 | 25.0 | 44.0 | 44.0 | 44.0 |
| **MSRP ($)** | 80,000 | 75,000 | 130,000 | 220,000 | 270,000 | 270,000 | 280,000 | 300,000 |
| **Range (km)** | 600 | 600 | 600 | 600 | 1,400 | 1,400 | 2,000 | 1,500 |
| **Fuel Efficiency (L/km)** | 0.28 | 0.28 | 0.28 | 0.32 | 0.32 | 0.35 | 0.35 | 0.35 |
| **Maintenance Cost ($/km)** | 0.2 | 0.02 | 0.02 | 0.025 | 0.025 | 0.03 | 0.03 | 0.03 |
| **Annual Registration ($/year)** | 653 | 653 | 653 | 653 | 653 | 6,872 | 6,872 | 6,872 |
| **Annual Distance (km/year)** | 23,000 | 23,000 | 23,000 | 23,000 | 23,000 | 84,000 | 84,000 | 84,000 |
| **Noise Pollution ($/km)** | 0.01 | 0.01 | 0.01 | 0.017 | 0.017 | 0.025 | 0.025 | 0.025 |
