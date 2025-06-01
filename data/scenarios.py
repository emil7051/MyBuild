"""
Economic and environmental scenarios for TCO modelling to enable scenario-based analysis with time-varying parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import numpy as np

# ============================================================================
# SCENARIO DATACLASSES
# ============================================================================

@dataclass
class EconomicScenario:
    """Defines economic parameters that vary over time."""
    
    name: str
    description: str
    
    # Price trajectories (as annual multipliers from base year)
    diesel_price_trajectory: List[float] = field(default_factory=list)
    electricity_price_trajectory: List[float] = field(default_factory=list)
    battery_price_trajectory: List[float] = field(default_factory=list)
    carbon_price_trajectory: List[float] = field(default_factory=list)
    
    # Technology improvement curves
    bev_efficiency_improvement: List[float] = field(default_factory=list)  # Annual improvement in kWh/km
    diesel_efficiency_improvement: List[float] = field(default_factory=list)  # Annual improvement in L/km
    
    # Maintenance cost trajectory
    maintenance_cost_multiplier: List[float] = field(default_factory=list)  # Multiplier for maintenance costs by year
    
    # Market factors
    bev_residual_value_multiplier: List[float] = field(default_factory=list)  # Adjustment to depreciation
    infrastructure_cost_trajectory: List[float] = field(default_factory=list)
    
    # Policy evolution
    policy_phase_out_year: Optional[int] = None  # Year when subsidies end
    road_user_charge_bev_start_year: Optional[int] = None  # Year when RUC applies to BEVs
    
    def __post_init__(self):
        """Validate and extend trajectories to standard vehicle life."""
        from data.constants import VEHICLE_LIFE
        
        # Extend all trajectories to vehicle life if shorter
        self._extend_trajectory('diesel_price_trajectory', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('electricity_price_trajectory', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('battery_price_trajectory', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('carbon_price_trajectory', VEHICLE_LIFE, 0.0)
        self._extend_trajectory('bev_efficiency_improvement', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('diesel_efficiency_improvement', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('maintenance_cost_multiplier', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('bev_residual_value_multiplier', VEHICLE_LIFE, 1.0)
        self._extend_trajectory('infrastructure_cost_trajectory', VEHICLE_LIFE, 1.0)
    
    def _extend_trajectory(self, attr_name: str, target_length: int, default_value: float):
        """Extend a trajectory list to target length."""
        trajectory = getattr(self, attr_name)
        if not trajectory:
            # If empty, create constant trajectory
            setattr(self, attr_name, [default_value] * target_length)
        elif len(trajectory) < target_length:
            # Extend with last value
            last_value = trajectory[-1]
            trajectory.extend([last_value] * (target_length - len(trajectory)))
            setattr(self, attr_name, trajectory)
    
    def get_diesel_price_multiplier(self, year: int) -> float:
        """Get diesel price multiplier for a specific year."""
        if 0 < year <= len(self.diesel_price_trajectory):
            return self.diesel_price_trajectory[year - 1]
        return 1.0
    
    def get_electricity_price_multiplier(self, year: int) -> float:
        """Get electricity price multiplier for a specific year."""
        if 0 < year <= len(self.electricity_price_trajectory):
            return self.electricity_price_trajectory[year - 1]
        return 1.0
    
    def get_battery_price_multiplier(self, year: int) -> float:
        """Get battery price multiplier for a specific year."""
        if 0 < year <= len(self.battery_price_trajectory):
            return self.battery_price_trajectory[year - 1]
        return 1.0
    
    def get_carbon_price(self, year: int) -> float:
        """Get carbon price for a specific year ($/tonne)."""
        if 0 < year <= len(self.carbon_price_trajectory):
            return self.carbon_price_trajectory[year - 1]
        return 0.0
    
    def policy_active(self, year: int) -> bool:
        """Check if policy incentives are active in a given year."""
        if self.policy_phase_out_year is None:
            return True
        return year < self.policy_phase_out_year
    
    def ruc_applies_bev(self, year: int) -> bool:
        """Check if road user charges apply to BEVs in a given year."""
        if self.road_user_charge_bev_start_year is None:
            return False
        return year >= self.road_user_charge_bev_start_year
    
    def get_maintenance_cost_multiplier(self, year: int) -> float:
        """Get maintenance cost multiplier for a specific year."""
        if 0 < year <= len(self.maintenance_cost_multiplier):
            return self.maintenance_cost_multiplier[year - 1]
        return 1.0


def generate_price_trajectory(
    base_growth_rate: float,
    years: int,
) -> List[float]:
    """
    Generate a price trajectory with optional volatility and shocks.
    
    Args:
        base_growth_rate: Annual growth rate (e.g., 0.03 for 3%)
        years: Number of years
    
    Returns:
        List of multipliers relative to base year
    """
    trajectory = [1.0]  # Base year = 1.0
    
    for year in range(2, years + 1):
        growth = base_growth_rate
        new_value = trajectory[-1] * (1 + growth)
        trajectory.append(new_value)
    
    return trajectory


def generate_maintenance_trajectory(years: int, start_multiplier: float = 0.85, end_multiplier: float = 1.25) -> List[float]:
    """
    Generate a maintenance cost trajectory that increases over vehicle life.
    
    Args:
        years: Number of years
        start_multiplier: Starting multiplier (default 0.85 = 15% below average)
        end_multiplier: Ending multiplier (default 1.25 = 25% above average)
    
    Returns:
        List of multipliers that increase linearly from start to end
    """
    if years == 1:
        return [1.0]
    
    # Linear interpolation from start to end
    return [start_multiplier + (end_multiplier - start_multiplier) * i / (years - 1) for i in range(years)]

# ============================================================================
# PRE-DEFINED SCENARIOS
# ============================================================================

SCENARIOS = {
    'baseline': EconomicScenario(
        name='Baseline',
        description='Current trajectory with moderate price increases',
        diesel_price_trajectory=generate_price_trajectory(0.03, 15),  # 3% annual increase
        electricity_price_trajectory=generate_price_trajectory(0.02, 15),  # 2% annual increase
        battery_price_trajectory=generate_price_trajectory(-0.07, 15),  # 7% annual decrease
        carbon_price_trajectory=[0] * 15,  # No carbon price
        bev_efficiency_improvement=generate_price_trajectory(-0.02, 15),  # 2% annual improvement
        diesel_efficiency_improvement=generate_price_trajectory(-0.01, 15),  # 1% annual improvement
        maintenance_cost_multiplier=generate_maintenance_trajectory(15),  # 0.85 to 1.25 over vehicle life
    ),
    
    'technology_breakthrough': EconomicScenario(
        name='Technology Breakthrough',
        description='Rapid battery technology improvement',
        diesel_price_trajectory=generate_price_trajectory(0.03, 15),
        electricity_price_trajectory=generate_price_trajectory(0.02, 15),
        battery_price_trajectory=[1.0, 0.85, 0.72, 0.61, 0.52, 0.44, 0.37, 0.32, 0.27, 0.23, 0.20, 0.17, 0.15, 0.13, 0.11],
        carbon_price_trajectory=[0] * 15,
        bev_efficiency_improvement=generate_price_trajectory(-0.04, 15),  # Major efficiency gains
        diesel_efficiency_improvement=generate_price_trajectory(-0.01, 15),
        bev_residual_value_multiplier=[1.0, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3],
        maintenance_cost_multiplier=generate_maintenance_trajectory(15),  # Same maintenance trajectory
    ),
    
    'oil_crisis': EconomicScenario(
        name='Oil Crisis',
        description='Major oil supply disruption in year 3',
        diesel_price_trajectory=[1.0, 1.03, 1.55, 1.60, 1.65, 1.70, 1.75, 1.80, 1.86, 1.91, 1.97, 2.03, 2.09, 2.15, 2.22],
        electricity_price_trajectory=generate_price_trajectory(0.03, 15),  # Electricity also affected
        battery_price_trajectory=generate_price_trajectory(-0.07, 15),
        carbon_price_trajectory=[0] * 15,
        bev_efficiency_improvement=generate_price_trajectory(-0.02, 15),
        diesel_efficiency_improvement=generate_price_trajectory(-0.02, 15),  # Faster improvement due to high prices
        maintenance_cost_multiplier=generate_maintenance_trajectory(15),  # Same maintenance trajectory
    ),
}

# ============================================================================
# SCENARIO FUNCTIONS
# ============================================================================

# Active scenario (default to baseline)
active_scenario: EconomicScenario = SCENARIOS['baseline']

def set_active_scenario(scenario_name: str):
    """Set the active economic scenario."""
    global active_scenario
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Scenario '{scenario_name}' not found. Available: {list(SCENARIOS.keys())}")
    active_scenario = SCENARIOS[scenario_name]


def get_active_scenario() -> EconomicScenario:
    """Get the currently active economic scenario."""
    return active_scenario


def create_custom_scenario(
    name: str,
    description: str,
    **kwargs
) -> EconomicScenario:
    """Create a custom economic scenario."""
    scenario = EconomicScenario(name=name, description=description, **kwargs)
    SCENARIOS[name] = scenario
    return scenario 