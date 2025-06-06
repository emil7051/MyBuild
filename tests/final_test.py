#!/usr/bin/env python3
"""Final test of report generation functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting report generation test...")

try:
    # Import everything we need
    from calculations.calculations import vehicle_data, compare_vehicle_pairs
    from data.scenarios import SCENARIOS
    from reports import (
        calculate_payback_analysis,
        create_payback_chart,
        generate_executive_summary,
        analyse_policy_combinations
    )
    
    print("✓ All imports successful!")
    
    # Test basic functionality
    print("\nTesting vehicle data retrieval...")
    bev = vehicle_data.get_vehicle('BEV006')
    diesel = vehicle_data.get_vehicle('DSL006')
    print(f"✓ Loaded vehicles: {bev.vehicle.model_name} vs {diesel.vehicle.model_name}")
    
    # Test payback analysis
    print("\nTesting payback analysis...")
    payback = calculate_payback_analysis(bev, diesel)
    print(f"✓ Payback calculated: {payback.payback_years:.1f} years" if payback.breakeven_achieved else "✓ Payback calculated: No breakeven")
    
    # Test comparisons
    print("\nTesting vehicle comparisons...")
    comparisons = compare_vehicle_pairs(SCENARIOS['baseline'])
    print(f"✓ Compared {len(comparisons)} vehicle pairs")
    
    # Test executive summary
    print("\nGenerating executive summary...")
    summary = generate_executive_summary(comparisons, 'Baseline Scenario')
    print(f"✓ Executive summary generated")
    print(f"  - Total pairs: {summary['overview']['total_vehicle_pairs']}")
    print(f"  - BEV competitive: {summary['overview']['percentage_competitive']:.1f}%")
    
    # Create chart
    print("\nCreating payback chart...")
    chart = create_payback_chart(payback)
    chart.write_html('payback_analysis.html')
    print("✓ Chart saved to payback_analysis.html")
    
    print("\n✅ All tests passed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
