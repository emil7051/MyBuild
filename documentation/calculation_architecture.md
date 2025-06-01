# TCO Calculation Architecture Documentation

## Overview

The Total Cost of Ownership (TCO) calculation system is designed to compare the economic viability of Battery Electric Vehicles (BEVs) versus Diesel vehicles for commercial trucking applications. The system uses a modular architecture with clear separation of concerns.

## Current Architecture

### 1. Data Layer

#### vehicles.py

- **Purpose**: Defines the core vehicle data model
- **Key Components**:
  - `VehicleModel` dataclass: Immutable vehicle specifications
  - `ALL_MODELS`: List of all vehicle instances
  - `BY_ID`: Dictionary for O(1) vehicle lookup
- **Data Includes**: MSRP, range, battery capacity, fuel consumption, maintenance costs, etc.

#### constants.py

- **Purpose**: Central repository for fixed calculation parameters
- **Key Categories**:
  - Financial parameters (interest rates, depreciation, financing terms)
  - Fuel/energy prices
  - Maintenance costs
  - Policy parameters
- **Note**: Currently uses fixed values, not time-varying

#### policies.py

- **Purpose**: Manages government incentives and policy interventions
- **Key Components**:
  - Policy dataclasses (PurchaseRebate, StampDutyExemption, etc.)
  - `POLICIES` dictionary: Central policy registry
  - Calculation functions for policy impacts
- **Features**:
  - Policies can be enabled/disabled
  - Supports various incentive types (rebates, tax exemptions, subsidies)

#### scenarios.py (NOT INTEGRATED)

- **Purpose**: Defines economic scenarios with time-varying parameters
- **Key Components**:
  - `EconomicScenario` dataclass: Contains price trajectories and technology curves
  - Pre-defined scenarios (baseline, technology breakthrough, oil crisis)
  - Trajectory generation functions
- **Status**: Exists but not connected to calculation pipeline

### 2. Pre-calculation Layer

#### inputs.py

- **Purpose**: Pre-calculates commonly used values to improve performance and consistency
- **Key Components**:
  - `VehicleInputs` class: Pre-calculates purchase costs, financing, fuel costs, etc.
  - `VehicleData` class: Manages all vehicle inputs as a singleton
  - Utility functions for transparent calculations
- **Calculations Include**:
  - Initial cost (MSRP + stamp duty - rebates)
  - Financing parameters (down payment, monthly payment, total cost)
  - Annual operating costs (fuel, maintenance, insurance)
  - Battery replacement costs
  - Depreciation schedules

### 3. Calculation Layer

#### calculations.py

- **Purpose**: Performs final TCO calculations using pre-calculated inputs
- **Key Components**:
  - `TCOResult` dataclass: Structured calculation results
  - `calculate_tco_from_inputs()`: Main calculation function
  - Comparison functions for BEV vs Diesel pairs
- **Process**:
  1. Uses pre-calculated values from VehicleInputs
  2. Applies time value of money (discounting)
  3. Sums all cost components over vehicle life
  4. Calculates per-year and per-km costs

## Current Data Flow

1. Vehicle Definition (vehicles.py)
   ↓
2. Policy Application (policies.py) + Constants (constants.py)
   ↓
3. Input Pre-calculation (inputs.py)
   ↓
4. TCO Calculation (calculations.py)
   ↓
5. Results (TCOResult)
