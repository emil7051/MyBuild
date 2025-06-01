"""
Test script to demonstrate the new inputs.py structure.
Shows how to access pre-calculated values transparently.
"""

from calculations.inputs import vehicle_data
from calculations.financial import calculate_stamp_duty, calculate_initial_cost
from calculations.calculations import calculate_tco_from_inputs
import data.constants as const


def demonstrate_inputs():
    """Demonstrate how the new inputs structure works."""
    
    # 1. Universal vehicle access
    print("=== Universal Vehicle Access ===")
    vehicle_inputs = vehicle_data.get_vehicle('BEV001')
    print(f"Vehicle: {vehicle_inputs.vehicle.model_name}")
    print(f"MSRP: ${vehicle_inputs.vehicle.msrp:,.2f}")
    print()
    
    # 2. Transparent subcomponent calculations
    print("=== Transparent Initial Cost Calculations ===")
    print(f"MSRP: ${vehicle_inputs.vehicle.msrp:,.2f}")
    print(f"+ Stamp Duty ({const.STAMP_DUTY_RATE:.1%}): ${vehicle_inputs.stamp_duty:,.2f}")
    if vehicle_inputs.rebate > 0:
        print(f"- BEV Rebate: ${vehicle_inputs.rebate:,.2f}")
    print(f"= Initial Cost: ${vehicle_inputs.initial_cost:,.2f}")
    print()
    
    # 3. Pre-calculated values available
    print("=== Pre-calculated Values ===")
    print(f"Down Payment: ${vehicle_inputs.down_payment:,.2f}")
    print(f"Loan Amount: ${vehicle_inputs.loan_amount:,.2f}")
    print(f"Monthly Payment: ${vehicle_inputs.monthly_payment:,.2f}")
    print(f"Total Financing Cost: ${vehicle_inputs.total_financing_cost:,.2f}")
    print()
    
    print(f"Annual Fuel Cost (Base): ${vehicle_inputs.annual_fuel_cost_base:,.2f}")
    print(f"Annual Maintenance Cost: ${vehicle_inputs.annual_maintenance_cost:,.2f}")
    print(f"Annual Insurance Cost: ${vehicle_inputs.annual_insurance_cost:,.2f}")
    print(f"  - Vehicle Insurance: ${vehicle_inputs.annual_vehicle_insurance:,.2f}")
    print(f"  - Other Insurance: ${const.OTHER_INSURANCE:,.2f}")
    print()
    
    # 4. Year-specific calculations
    print("=== Year-specific Calculations ===")
    for year in [1, 5, 8, 10]:
        fuel_cost = vehicle_inputs.get_fuel_cost_year(year)
        battery_cost = vehicle_inputs.get_battery_replacement_year(year)
        print(f"Year {year}:")
        print(f"  - Fuel Cost: ${fuel_cost:,.2f}")
        if battery_cost > 0:
            print(f"  - Battery Replacement: ${battery_cost:,.2f}")
    print()
    
    # 5. TCO calculation using inputs
    print("=== TCO Calculation ===")
    tco_result = calculate_tco_from_inputs(vehicle_inputs)
    print(f"Total Cost: ${tco_result.total_cost:,.2f}")
    print(f"Annual Cost: ${tco_result.annual_cost:,.2f}")
    print(f"Cost per km: ${tco_result.cost_per_km:.3f}")
    print()
    
    # 6. Compare BEV vs Diesel pair
    print("=== BEV vs Diesel Comparison ===")
    diesel_inputs = vehicle_data.get_vehicle(vehicle_inputs.vehicle.comparison_pair)
    diesel_tco = calculate_tco_from_inputs(diesel_inputs)
    
    print(f"BEV ({vehicle_inputs.vehicle.model_name}):")
    print(f"  - Initial Cost: ${vehicle_inputs.initial_cost:,.2f}")
    print(f"    • MSRP: ${vehicle_inputs.vehicle.msrp:,.2f}")
    print(f"    • Stamp Duty: ${vehicle_inputs.stamp_duty:,.2f}")
    if vehicle_inputs.rebate > 0:
        print(f"    • Rebate: -${vehicle_inputs.rebate:,.2f}")
    print(f"  - Annual Operating Costs:")
    print(f"    • Fuel: ${vehicle_inputs.annual_fuel_cost_base:,.2f}")
    print(f"    • Maintenance: ${vehicle_inputs.annual_maintenance_cost:,.2f}")
    print(f"    • Insurance: ${vehicle_inputs.annual_insurance_cost:,.2f}")
    print(f"    • Registration: ${vehicle_inputs.vehicle.annual_registration:,.2f}")
    print(f"  - Total TCO: ${tco_result.total_cost:,.2f}")
    print(f"  - Annual Cost: ${tco_result.annual_cost:,.2f}")
    
    print(f"\nDiesel ({diesel_inputs.vehicle.model_name}):")
    print(f"  - Initial Cost: ${diesel_inputs.initial_cost:,.2f}")
    print(f"    • MSRP: ${diesel_inputs.vehicle.msrp:,.2f}")
    print(f"    • Stamp Duty: ${diesel_inputs.stamp_duty:,.2f}")
    print(f"  - Annual Operating Costs:")
    print(f"    • Fuel: ${diesel_inputs.annual_fuel_cost_base:,.2f}")
    print(f"    • Maintenance: ${diesel_inputs.annual_maintenance_cost:,.2f}")
    print(f"    • Insurance: ${diesel_inputs.annual_insurance_cost:,.2f}")
    print(f"    • Registration: ${diesel_inputs.vehicle.annual_registration:,.2f}")
    print(f"  - Total TCO: ${diesel_tco.total_cost:,.2f}")
    print(f"  - Annual Cost: ${diesel_tco.annual_cost:,.2f}")
    
    print(f"\nDifference (BEV - Diesel):")
    print(f"  - Initial Cost: ${vehicle_inputs.initial_cost - diesel_inputs.initial_cost:,.2f}")
    print(f"  - Total TCO: ${tco_result.total_cost - diesel_tco.total_cost:,.2f}")
    print(f"  - Annual Cost: ${tco_result.annual_cost - diesel_tco.annual_cost:,.2f}")


def demonstrate_utility_functions():
    """Demonstrate standalone utility functions."""
    print("\n=== Utility Functions ===")
    
    # Example MSRP
    msrp = 200000
    
    stamp_duty = calculate_stamp_duty(msrp)
    initial_cost_bev = calculate_initial_cost(msrp, 'BEV')
    initial_cost_diesel = calculate_initial_cost(msrp, 'Diesel')
    
    print(f"For a vehicle with MSRP ${msrp:,.2f}:")
    print(f"  - Stamp Duty: ${stamp_duty:,.2f}")
    print(f"  - Initial Cost (BEV): ${initial_cost_bev:,.2f}")
    print(f"  - Initial Cost (Diesel): ${initial_cost_diesel:,.2f}")
    print(f"Note: Insurance is an annual operating expense, not part of initial cost")


if __name__ == "__main__":
    demonstrate_inputs()
    demonstrate_utility_functions() 