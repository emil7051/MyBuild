# Policy Incentive System

This module provides a flexible framework for modelling various policy incentives and disincentives to encourage the adoption of battery electric trucks.

## Overview

The policy system is implemented in `data/policies.py` and integrates with the existing TCO calculations. Each policy can be individually enabled/disabled and configured with specific parameters.

## Available Policies

### BEV Incentives

1. **Fixed Purchase Rebate**
   - Direct cash rebate for BEV purchases
   - Parameter: `amount` ($ AUD)

2. **Percentage Purchase Rebate**
   - Percentage-based rebate on vehicle price
   - Parameters: `percentage` (decimal), `max_amount` (optional cap)

3. **Stamp Duty Exemption**
   - Full or partial exemption from stamp duty
   - Parameter: `exemption_percentage` (decimal, 1.0 = 100% exemption)

4. **Interest Rate Subsidy**
   - Reduced financing interest rate for BEVs
   - Parameter: `rate_reduction` (percentage points)

5. **Charging Infrastructure Grant**
   - Grant for installing charging infrastructure
   - Parameters: `grant_percentage` (decimal), `max_amount` (optional cap)

6. **Accelerated Depreciation**
   - Enhanced first-year depreciation rate
   - Parameter: `first_year_rate` (decimal)

### Diesel Disincentives

1. **Zero Emission Zone Charge**
   - Annual charge for operating diesel vehicles in designated zones
   - Parameter: `annual_charge` ($ AUD)

2. **Carbon Pricing**
   - Carbon tax based on emissions
   - Parameter: `price_per_tonne` ($ AUD per tonne CO2e)

## Usage Examples

### Basic Usage

```python
from data import policies

# Enable a single policy
policies.POLICIES['purchase_rebate'].enabled = True
policies.POLICIES['purchase_rebate'].amount = 20000

# Disable all policies
policies.disable_all_policies()

# Enable preset scenarios
policies.enable_standard_incentives()
policies.enable_aggressive_incentives()
```

### Custom Policy Mix

```python
# Create a custom policy combination
policies.disable_all_policies()

# 15% purchase rebate, capped at $40,000
policies.POLICIES['percentage_rebate'].enabled = True
policies.POLICIES['percentage_rebate'].percentage = 0.15
policies.POLICIES['percentage_rebate'].max_amount = 40000

# 100% stamp duty exemption
policies.POLICIES['stamp_duty_exemption'].enabled = True
policies.POLICIES['stamp_duty_exemption'].exemption_percentage = 1.0

# $50/tonne carbon price
policies.POLICIES['carbon_pricing'].enabled = True
policies.POLICIES['carbon_pricing'].price_per_tonne = 50
```

### Integration with Calculations

The policy system automatically integrates with the TCO calculations:

```python
from calculations.inputs import vehicle_data

# Policies affect vehicle calculations automatically
vehicle = vehicle_data.get_vehicle("volvo_fm_electric")
print(f"Rebate applied: ${vehicle.rebate:,.0f}")
print(f"Initial cost after policies: ${vehicle.initial_cost:,.0f}")
```

### Running Policy Scenarios

See `scripts/policy_example.py` for a complete example of running different policy scenarios and comparing their impacts.

## Policy Impact Functions

The module provides several calculation functions:

- `calculate_bev_purchase_rebate()`: Total purchase rebate combining all active rebate policies
- `calculate_stamp_duty_with_exemption()`: Stamp duty after exemptions
- `calculate_financing_interest_rate()`: Interest rate after subsidies
- `calculate_annual_policy_charges()`: Annual charges/credits from policies
- `calculate_infrastructure_grant()`: Infrastructure grant amount
- `get_depreciation_rate_first_year()`: First-year depreciation rate

## Adding New Policies

To add a new policy:

1. Create a new dataclass inheriting from `PolicyIncentive`
2. Add validation logic in the `validate()` method
3. Add an instance to the `POLICIES` dictionary
4. Create calculation functions as needed
5. Update relevant parts of the calculation system to use the new policy

## Notes

- All policies default to disabled (`enabled=False`)
- Policy parameters are validated when enabled
- Policies can be combined for cumulative effects
- The system maintains backward compatibility with existing constants
- Vehicle data must be reinitialised after policy changes to recalculate costs
