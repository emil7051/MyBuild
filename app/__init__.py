"""
Calculations module for TCO analysis.

Provides transparent access to vehicle inputs and TCO calculations.
"""

# Import key components for easy access
from calculations.inputs import (
    vehicle_data,
    VehicleInputs,
    VehicleData,
    calculate_financing_cost  # Legacy function
)

from calculations.financial import (
    calculate_stamp_duty,
    calculate_initial_cost
)

from calculations.utils import (
    calculate_present_value,
    discount_to_present
)

from calculations.calculations import (
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
    
    # Utility functions
    'calculate_stamp_duty',
    'calculate_initial_cost',
    'calculate_financing_cost',
    'calculate_present_value',
    'discount_to_present',
    
    # TCO calculations
    'TCOResult',
    'calculate_tco',
    'calculate_tco_from_inputs',
    'calculate_all_tcos',
    'compare_vehicle_pairs'
] 