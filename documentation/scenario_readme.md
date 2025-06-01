# Economic Scenarios Guide for MyBuild TCO Model

The scenarios system allows you to model different economic and technological futures for TCO calculations. Each scenario defines how key parameters (fuel prices, electricity costs, battery prices, etc.) change over the vehicle's lifetime.

## Using Pre-defined Scenarios

```python
from data.scenarios import set_active_scenario, get_active_scenario

# Switch to a different scenario
set_active_scenario('technology_breakthrough')

# Check current scenario
current = get_active_scenario()
print(f"Active scenario: {current.name}")
print(f"Description: {current.description}")
```

### Available Pre-defined Scenarios

1. **baseline**: Current trajectory with moderate price increases
   - Diesel: 3% annual increase
   - Electricity: 2% annual increase
   - Battery costs: 7% annual decrease
   - No carbon pricing

2. **technology_breakthrough**: Rapid battery technology improvement
   - Accelerated battery cost reductions
   - 4% annual BEV efficiency improvements
   - Improved BEV residual values

3. **oil_crisis**: Major oil supply disruption in year 3
   - Diesel prices spike 50% in year 3
   - Continued high growth thereafter
   - Faster diesel efficiency improvements due to price pressure

## Modifying Existing Scenarios

### Method 1: Direct Modification (Temporary)

```python
from data.scenarios import SCENARIOS

# Modify the baseline scenario
baseline = SCENARIOS['baseline']
baseline.carbon_price_trajectory = [0, 0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325]
baseline.road_user_charge_bev_start_year = 5
```

## Creating Custom Scenarios

### Method 1: Using create_custom_scenario

```python
from data.scenarios import create_custom_scenario, generate_price_trajectory

# Create a high electrification scenario
custom = create_custom_scenario(
    name='High Electrification',
    description='Rapid shift to renewable electricity',
    diesel_price_trajectory=generate_price_trajectory(0.04, 15),  # 4% growth
    electricity_price_trajectory=generate_price_trajectory(-0.02, 15),  # 2% decrease
    battery_price_trajectory=generate_price_trajectory(-0.10, 15),  # 10% decrease
    carbon_price_trajectory=[0, 0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650],
    bev_efficiency_improvement=generate_price_trajectory(-0.03, 15),
    diesel_efficiency_improvement=generate_price_trajectory(-0.01, 15),
    policy_phase_out_year=8,  # Subsidies end in year 8
    road_user_charge_bev_start_year=6  # RUC for BEVs starts year 6
)

# Activate the custom scenario
set_active_scenario('High Electrification')
```

### Method 2: Direct Instantiation

```python
from data.scenarios import EconomicScenario, SCENARIOS

# Create scenario with manual trajectories
volatile_scenario = EconomicScenario(
    name='Volatile Markets',
    description='High price volatility and uncertainty',
    diesel_price_trajectory=[1.0, 1.1, 0.9, 1.3, 1.2, 1.5, 1.4, 1.8, 1.6, 2.0, 1.9, 2.2, 2.1, 2.4, 2.3],
    electricity_price_trajectory=[1.0, 1.05, 1.02, 1.08, 1.06, 1.12, 1.10, 1.15, 1.13, 1.18, 1.16, 1.21, 1.19, 1.24, 1.22],
    battery_price_trajectory=[1.0, 0.92, 0.88, 0.82, 0.78, 0.72, 0.68, 0.62, 0.58, 0.52, 0.48, 0.42, 0.38, 0.32, 0.28],
    bev_residual_value_multiplier=[1.0, 0.95, 0.90, 0.95, 1.0, 1.05, 1.0, 1.05, 1.1, 1.05, 1.1, 1.15, 1.1, 1.15, 1.2]
)

# Add to available scenarios
SCENARIOS['volatile'] = volatile_scenario
```

## Understanding Trajectory Values

All trajectories use **multipliers** relative to base year values (except carbon price):

- **Price trajectories**: 1.0 = base year price, 1.5 = 50% increase, 0.8 = 20% decrease
- **Efficiency improvements**: Values < 1.0 mean improvement (e.g., 0.98 = 2% better efficiency)
- **Carbon price**: Absolute values in $/tonne CO2
- **Residual value multiplier**: Adjusts depreciation calculations (>1.0 = better resale value)

## Integration with TCO Calculations

The TCO calculations automatically use the active scenario:

```python
from data.scenarios import set_active_scenario, get_active_scenario
from calculations.calculator import calculate_tco

# Set scenario
set_active_scenario('oil_crisis')

# Calculate TCO - will use oil crisis fuel prices
results = calculate_tco(vehicle_data)

# Access scenario data in calculations
scenario = get_active_scenario()
year_3_diesel_multiplier = scenario.get_diesel_price_multiplier(3)  # Returns 1.55
```

## Advanced: Policy Parameters

Scenarios can model policy changes:

```python
# Create scenario with policy phase-out
policy_scenario = create_custom_scenario(
    name='Policy Transition',
    description='Government incentives phase out over time',
    diesel_price_trajectory=generate_price_trajectory(0.03, 15),
    electricity_price_trajectory=generate_price_trajectory(0.02, 15),
    battery_price_trajectory=generate_price_trajectory(-0.07, 15),
    policy_phase_out_year=5,  # Subsidies end after year 4
    road_user_charge_bev_start_year=7  # BEVs start paying RUC in year 7
)

## Example: Complete Workflow

```python
from data.scenarios import create_custom_scenario, set_active_scenario, SCENARIOS
from calculations.calculator import calculate_tco
import pandas as pd

# 1. Create a custom scenario
green_transition = create_custom_scenario(
    name='Green Transition',
    description='Aggressive decarbonisation with carbon pricing',
    diesel_price_trajectory=[1.0, 1.04, 1.08, 1.12, 1.17, 1.22, 1.27, 1.32, 1.38, 1.44, 1.50, 1.56, 1.63, 1.70, 1.77],
    electricity_price_trajectory=[1.0, 0.99, 0.98, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.91, 0.90, 0.89, 0.88, 0.87, 0.86],
    battery_price_trajectory=[1.0, 0.90, 0.81, 0.73, 0.66, 0.59, 0.53, 0.48, 0.43, 0.39, 0.35, 0.31, 0.28, 0.25, 0.23],
    carbon_price_trajectory=[0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350],
    bev_efficiency_improvement=[1.0, 0.97, 0.94, 0.91, 0.88, 0.86, 0.83, 0.81, 0.78, 0.76, 0.74, 0.72, 0.70, 0.68, 0.66],
    policy_phase_out_year=10,
    road_user_charge_bev_start_year=8
)

# 2. Compare scenarios
results = {}
for scenario_name in ['baseline', 'green_transition', 'oil_crisis']:
    set_active_scenario(scenario_name)
    tco_results = calculate_tco(vehicle_data)
    results[scenario_name] = tco_results

# 3. Analyse results
comparison_df = pd.DataFrame(results)
print("TCO Comparison Across Scenarios:")
print(comparison_df)
```

## Troubleshooting

**Q: My trajectories are shorter than vehicle life?**
A: The system automatically extends trajectories using the last value. Alternatively, use `generate_price_trajectory()` to create full-length trajectories.

**Q: Can I have different scenarios for different vehicle types?**
A: The current system uses one active scenario. For vehicle-specific scenarios, modify the calculator to accept scenario parameters directly.
