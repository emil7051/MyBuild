"""
Calculations module for TCO analysis.

Provides transparent access to vehicle inputs and TCO calculations.
"""

# Import key components for easy access
from .inputs import (
    vehicle_data,
    VehicleInputs,
    VehicleData,
)

# Import from modular structure
from .financial import (
    calculate_stamp_duty,
    calculate_rebate,
    calculate_initial_cost,
    FinancingCalculator,
    DepreciationCalculator
)

from .operating import (
    FuelCostCalculator,
    ChargingTimeCostCalculator,
    MaintenanceCostCalculator,
    InsuranceCostCalculator,
    BatteryReplacementCalculator,
    calculate_carbon_cost_year
)

from .utils import (
    calculate_present_value,
    discount_to_present,
    calculate_npv_of_payments,
    calculate_annualised_cost,
    escalate_cost
)

from .calculations import (
    TCOResult,
    calculate_tco,
    calculate_tco_from_inputs,
    calculate_all_tcos,
    compare_vehicle_pairs
)

__all__ = [
    # Data access
    'vehicle_data',
    'VehicleInputs',
    'VehicleData',
    
    # Financial calculations
    'calculate_stamp_duty',
    'calculate_rebate',
    'calculate_initial_cost',
    'FinancingCalculator',
    'DepreciationCalculator',
    
    # Operating calculations
    'FuelCostCalculator',
    'ChargingTimeCostCalculator',
    'MaintenanceCostCalculator',
    'InsuranceCostCalculator',
    'BatteryReplacementCalculator',
    'calculate_carbon_cost_year',
    
    # Financial utilities
    'calculate_present_value',
    'discount_to_present',
    'calculate_npv_of_payments',
    'calculate_annualised_cost',
    'escalate_cost',
    
    # TCO calculations
    'TCOResult',
    'calculate_tco',
    'calculate_tco_from_inputs',
    'calculate_all_tcos',
    'compare_vehicle_pairs'
] 