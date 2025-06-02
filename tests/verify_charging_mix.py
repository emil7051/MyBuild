#!/usr/bin/env python3
"""Verify weight-class-specific charging mix implementation."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.vehicles import BY_ID
from calculations import vehicle_data
import data.constants as const

print("Verifying Weight-Class-Specific Charging Mix Implementation")
print("=" * 70)

# Test vehicles from different weight classes
test_vehicles = [
    ('BEV001', 'Light Rigid'),
    ('BEV004', 'Medium Rigid'),
    ('BEV006', 'Articulated'),
]

for vehicle_id, expected_class in test_vehicles:
    vehicle = BY_ID[vehicle_id]
    vehicle_inputs = vehicle_data.get_vehicle(vehicle_id)
    
    print(f"\n{vehicle.model_name} ({vehicle.weight_class}):")
    print(f"  - Annual kms: {vehicle.annual_kms:,}")
    print(f"  - kWh/km: {vehicle.kwh_per_km}")
    
    # Show which charging mix is being used
    if vehicle.weight_class == 'Articulated':
        print(f"  - Using ARTICULATED charging mix:")
        print(f"    * Off-peak: {const.ART_OFFPEAK_PROPORTION * 100:.0f}%")
        print(f"    * Public: {const.ART_PUBLIC_PROPORTION * 100:.0f}%")
    else:
        print(f"  - Using RIGID charging mix:")
        print(f"    * Off-peak: {const.RIGID_OFFPEAK_PROPORTION * 100:.0f}%")
        print(f"    * Public: {const.RIGID_PUBLIC_PROPORTION * 100:.0f}%")
    
    print(f"  - Annual fuel cost (year 1): ${vehicle_inputs.get_fuel_cost_year(1):,.2f}")

print("\n" + "=" * 70)
print("Key Difference:")
print(f"Articulated trucks use {(const.ART_PUBLIC_PROPORTION - const.RIGID_PUBLIC_PROPORTION) * 100:.0f}% more public charging")
print("This reflects their longer-distance operations requiring more en-route charging") 