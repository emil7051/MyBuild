"""
Test script to demonstrate the purchase method toggle functionality.
"""

from calculations.calculations import calculate_tco
from data.vehicles import BY_ID

# Get a sample vehicle (assuming there's at least one vehicle in the database)
sample_vehicle_id = list(BY_ID.keys())[0]
sample_vehicle = BY_ID[sample_vehicle_id]

print(f"Testing TCO calculation for {sample_vehicle.model} ({sample_vehicle.drivetrain_type})")
print("=" * 70)

# Calculate TCO with financing (default)
tco_financed = calculate_tco(sample_vehicle, purchase_method='financed')
print("\nFinanced Purchase:")
print(f"  Upfront payment (down payment): ${tco_financed.purchase_cost:,.2f}")
print(f"  Financing cost: ${tco_financed.financing_cost:,.2f}")
print(f"  Total TCO: ${tco_financed.total_cost:,.2f}")
print(f"  Annual cost: ${tco_financed.annual_cost:,.2f}")
print(f"  Cost per km: ${tco_financed.cost_per_km:.3f}")

# Calculate TCO with outright purchase
tco_outright = calculate_tco(sample_vehicle, purchase_method='outright')
print("\nOutright Purchase:")
print(f"  Upfront payment (full price): ${tco_outright.purchase_cost:,.2f}")
print(f"  Financing cost: ${tco_outright.financing_cost:,.2f}")
print(f"  Total TCO: ${tco_outright.total_cost:,.2f}")
print(f"  Annual cost: ${tco_outright.annual_cost:,.2f}")
print(f"  Cost per km: ${tco_outright.cost_per_km:.3f}")

# Compare the difference
print("\nComparison:")
print(f"  Upfront payment difference: ${tco_outright.purchase_cost - tco_financed.purchase_cost:,.2f}")
print(f"  Total TCO difference: ${tco_outright.total_cost - tco_financed.total_cost:,.2f}")
print(f"  (Negative means outright is cheaper)") 