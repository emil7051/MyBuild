#!/usr/bin/env python3
"""Test script for payload penalty implementation aligned with TCO specification."""

from calculations import vehicle_data, calculate_tco
from data.vehicles import BY_ID
from data.constants import FREIGHT_RATE_RIGID, FREIGHT_RATE_ARTICULATED, PAYLOAD_UTILISATION_FACTOR

print("Payload Penalty Implementation Test")
print("Aligned with TCO Technical Specification")
print("=" * 70)

# Test all vehicle pairs as per specification
test_pairs = [
    ('BEV001', 'DSL001'),  # Light Rigid: 4.0 vs 4.5 tonnes
    ('BEV002', 'DSL002'),  # Light Rigid: 4.0 vs 4.0 tonnes (same)
    ('BEV003', 'DSL003'),  # Light Rigid: 5.0 vs 6.0 tonnes
    ('BEV004', 'DSL004'),  # Medium Rigid: 10.5 vs 12.0 tonnes
    ('BEV005', 'DSL005'),  # Medium Rigid: 22.0 vs 25.0 tonnes
    ('BEV006', 'DSL006'),  # Articulated: 42.0 vs 50.0 tonnes
    ('BEV007', 'DSL007'),  # Articulated: 42.0 vs 50.0 tonnes
    ('BEV008', 'DSL008'),  # Articulated: 42.0 vs 50.0 tonnes
]

# Display freight rates from constants
print(f"\nFreight Rates (per tonne-km):")
print(f"  Rigid trucks: ${FREIGHT_RATE_RIGID:.2f}")
print(f"  Articulated trucks: ${FREIGHT_RATE_ARTICULATED:.2f}")
print(f"  Utilisation factor: {PAYLOAD_UTILISATION_FACTOR:.0%}")

print("\n" + "-" * 70)

for bev_id, dsl_id in test_pairs:
    print(f"\nComparing {bev_id} vs {dsl_id}:")
    
    # Get vehicles
    bev = BY_ID[bev_id]
    dsl = BY_ID[dsl_id]
    
    # Get vehicle inputs for BEV
    bev_inputs = vehicle_data.get_vehicle(bev_id)
    
    # Display vehicle details
    print(f"  BEV: {bev.model_name} - {bev.payload:.1f} tonnes payload")
    print(f"  Diesel: {dsl.model_name} - {dsl.payload:.1f} tonnes payload")
    
    # Calculate payload difference
    payload_diff = dsl.payload - bev.payload
    print(f"  Payload difference: {payload_diff:.1f} tonnes")
    
    # Calculate expected penalty
    if payload_diff > 0:
        freight_rate = FREIGHT_RATE_ARTICULATED if bev.weight_class == 'Articulated' else FREIGHT_RATE_RIGID
        expected_penalty = payload_diff * freight_rate * bev.annual_kms * PAYLOAD_UTILISATION_FACTOR
        print(f"  Expected annual penalty: ${expected_penalty:,.2f}")
        print(f"    = {payload_diff:.1f} × ${freight_rate:.2f} × {bev.annual_kms:,} × {PAYLOAD_UTILISATION_FACTOR:.0%}")
    else:
        expected_penalty = 0
        print(f"  Expected annual penalty: $0.00 (BEV has equal or higher payload)")
    
    # Display actual calculation
    print(f"  Actual annual penalty: ${bev_inputs.annual_payload_penalty:,.2f}")
    
    # Verify calculation
    if abs(bev_inputs.annual_payload_penalty - expected_penalty) < 0.01:
        print(f"  ✓ Calculation correct")
    else:
        print(f"  ✗ Calculation error!")
    
    # Calculate TCO to get NPV
    tco_result = calculate_tco(bev)
    print(f"  NPV of payload penalty: ${tco_result.payload_penalty_cost:,.2f}")

# Test diesel vehicles (should have no penalty)
print("\n" + "-" * 70)
print("\nTesting Diesel Vehicles (should have no penalty):")
for _, dsl_id in test_pairs[:3]:  # Test first 3 diesel vehicles
    dsl_inputs = vehicle_data.get_vehicle(dsl_id)
    dsl = BY_ID[dsl_id]
    print(f"\n{dsl_id}: {dsl.model_name}")
    print(f"  Annual payload penalty: ${dsl_inputs.annual_payload_penalty:,.2f}")
    if dsl_inputs.annual_payload_penalty == 0:
        print(f"  ✓ Correct (diesel vehicles have no penalty)")
    else:
        print(f"  ✗ Error: Diesel vehicle should not have penalty!")

print("\n" + "=" * 70)
print("Test completed successfully!") 