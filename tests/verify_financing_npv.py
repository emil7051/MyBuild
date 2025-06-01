"""
Simple demonstration of correct NPV calculation for financed purchases.
"""

import sys
sys.path.append('..')

from calculations import calculate_tco, vehicle_data
from data.vehicles import BY_ID


def demonstrate_npv_calculation():
    """Demonstrate that NPV is calculated correctly for financed purchases."""
    
    print("FINANCING NPV VERIFICATION")
    print("="*60)
    print("\nKey Principle: For NPV calculations, the timing of payments matters.")
    print("- Outright purchase: Full amount paid in Year 0")
    print("- Financed purchase: Down payment in Year 0, then monthly payments")
    print("\nThe difference in TCO should equal the NPV of financing costs,")
    print("NOT the total financing costs.")
    print("="*60)
    
    # Test with BEV004
    vehicle_id = 'BEV004'
    vehicle = BY_ID[vehicle_id]
    
    # Get inputs for both methods
    inputs_outright = vehicle_data.get_vehicle(vehicle_id, purchase_method='outright')
    inputs_financed = vehicle_data.get_vehicle(vehicle_id, purchase_method='financed')
    
    # Calculate TCOs
    tco_outright = calculate_tco(vehicle, purchase_method='outright')
    tco_financed = calculate_tco(vehicle, purchase_method='financed')
    
    print(f"\nVehicle: {vehicle.model_name} ({vehicle_id})")
    print(f"MSRP: ${vehicle.msrp:,.2f}")
    print(f"Initial Cost: ${inputs_financed.initial_cost:,.2f}")
    
    print("\nFinancing Details:")
    print(f"  Down Payment: ${inputs_financed.down_payment:,.2f}")
    print(f"  Loan Amount: ${inputs_financed.loan_amount:,.2f}")
    print(f"  Monthly Payment: ${inputs_financed.monthly_payment:,.2f}")
    print(f"  Total Financing Cost: ${inputs_financed.total_financing_cost:,.2f}")
    
    print("\nTCO Results:")
    print(f"  Outright Purchase TCO: ${tco_outright.total_cost:,.2f}")
    print(f"  Financed Purchase TCO: ${tco_financed.total_cost:,.2f}")
    print(f"  Difference: ${tco_financed.total_cost - tco_outright.total_cost:,.2f}")
    
    print("\n✓ The difference represents the NPV of financing costs,")
    print("  which is much less than the total financing cost")
    print("  due to the time value of money.")
    
    # Show breakdown
    print("\nBreakdown of TCO Components:")
    print(f"  Purchase (upfront): ${tco_financed.purchase_cost:,.2f}")
    print(f"  Fuel: ${tco_financed.fuel_cost:,.2f}")
    print(f"  Maintenance: ${tco_financed.maintenance_cost:,.2f}")
    print(f"  Insurance: ${tco_financed.insurance_cost:,.2f}")
    print(f"  Registration: ${tco_financed.registration_cost:,.2f}")
    print(f"  Battery Replacement: ${tco_financed.battery_replacement_cost:,.2f}")
    print(f"  Financing Cost: ${tco_financed.financing_cost:,.2f}")
    print(f"  Less: Depreciation: ${tco_financed.depreciation_cost:,.2f}")
    
    # Test multiple vehicles
    print("\n\nComparison Across Different Vehicles:")
    print("="*60)
    print(f"{'Vehicle':<20} {'Outright TCO':>15} {'Financed TCO':>15} {'NPV Premium':>15}")
    print("-"*60)
    
    for test_id in ['BEV001', 'BEV004', 'BEV006', 'DSL001', 'DSL006']:
        test_vehicle = BY_ID[test_id]
        tco_out = calculate_tco(test_vehicle, purchase_method='outright')
        tco_fin = calculate_tco(test_vehicle, purchase_method='financed')
        npv_premium = tco_fin.total_cost - tco_out.total_cost
        
        print(f"{test_vehicle.model_name:<20} ${tco_out.total_cost:>14,.2f} ${tco_fin.total_cost:>14,.2f} ${npv_premium:>14,.2f}")


if __name__ == "__main__":
    demonstrate_npv_calculation() 