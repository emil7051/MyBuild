#!/usr/bin/env python3
"""Quick test to verify the import fix worked."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports after fix...")

try:
    from reports import (
        calculate_payback_analysis,
        create_payback_chart,
        generate_executive_summary,
        analyse_policy_combinations
    )
    print("✓ All imports successful!")
    
    # Quick test
    from calculations.calculations import vehicle_data
    bev = vehicle_data.get_vehicle('BEV006')
    diesel = vehicle_data.get_vehicle('DSL006')
    print(f"✓ Loaded vehicles: {bev.name} vs {diesel.name}")
    
except Exception as e:
    print(f"✗ Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
