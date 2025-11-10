"""
Calculations module for TCO analysis.

Provides transparent access to vehicle inputs and TCO calculations.
"""

from .calculations import (
    TCOResult,
    calculate_all_tcos,
    calculate_tco,
    calculate_tco_from_inputs,
    compare_vehicle_pairs,
)

# Import from modular structure
from .financial import (
    DepreciationCalculator,
    FinancingCalculator,
    calculate_initial_cost,
    calculate_rebate,
    calculate_stamp_duty,
)

# Import key components for easy access
from .inputs import VehicleData, VehicleInputs, vehicle_data
from .operating import (
    BatteryReplacementCalculator,
    ChargingTimeCostCalculator,
    FuelCostCalculator,
    InsuranceCostCalculator,
    MaintenanceCostCalculator,
    PayloadPenaltyCalculator,
    calculate_carbon_cost_year,
)
from .simulation import (
    MonteCarloSimulation,
    SensitivityAnalysis,
    SimulationResults,
    UncertaintyParameter,
)
from .utils import (
    calculate_annualised_cost,
    calculate_npv_of_payments,
    calculate_present_value,
    discount_to_present,
    escalate_cost,
)

__all__ = [
    # Data access
    "vehicle_data",
    "VehicleInputs",
    "VehicleData",
    # Financial calculations
    "calculate_stamp_duty",
    "calculate_rebate",
    "calculate_initial_cost",
    "FinancingCalculator",
    "DepreciationCalculator",
    # Operating calculations
    "FuelCostCalculator",
    "ChargingTimeCostCalculator",
    "MaintenanceCostCalculator",
    "InsuranceCostCalculator",
    "BatteryReplacementCalculator",
    "PayloadPenaltyCalculator",
    "calculate_carbon_cost_year",
    # Financial utilities
    "calculate_present_value",
    "discount_to_present",
    "calculate_npv_of_payments",
    "calculate_annualised_cost",
    "escalate_cost",
    # TCO calculations
    "TCOResult",
    "calculate_tco",
    "calculate_tco_from_inputs",
    "calculate_all_tcos",
    "compare_vehicle_pairs",
    # Simulation and uncertainty analysis exports
    "UncertaintyParameter",
    "SimulationResults",
    "MonteCarloSimulation",
    "SensitivityAnalysis",
]
