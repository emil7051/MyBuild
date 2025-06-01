"""
Simple example showing the transparency of the new inputs structure.
"""

from calculations import vehicle_data, calculate_tco_from_inputs


def main():
    # Access any vehicle universally
    vehicle = vehicle_data.get_vehicle('BEV001')
    
    # All subcomponents are pre-calculated and transparent
    print(f"Vehicle: {vehicle.vehicle.model_name}")
    print(f"MSRP: ${vehicle.vehicle.msrp:,.2f}")
    print(f"Stamp Duty: ${vehicle.stamp_duty:,.2f}")
    print(f"Initial Cost: ${vehicle.initial_cost:,.2f}")
    
    # Calculate TCO using the pre-calculated inputs
    tco = calculate_tco_from_inputs(vehicle)
    print(f"\nTotal Cost of Ownership: ${tco.total_cost:,.2f}")
    print(f"Annual Cost: ${tco.annual_cost:,.2f}")
    print(f"Cost per km: ${tco.cost_per_km:.3f}")
    
    # Compare with diesel equivalent
    print("\n--- Comparison with Diesel ---")
    diesel = vehicle_data.get_vehicle(vehicle.vehicle.comparison_pair)
    diesel_tco = calculate_tco_from_inputs(diesel)
    
    print(f"BEV TCO: ${tco.total_cost:,.2f}")
    print(f"Diesel TCO: ${diesel_tco.total_cost:,.2f}")
    print(f"Savings: ${diesel_tco.total_cost - tco.total_cost:,.2f}")


if __name__ == "__main__":
    main() 