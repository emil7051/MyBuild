"""Test script to verify scenario integration in TCO calculations."""

import sys
sys.path.append('.')

from data.scenarios import SCENARIOS, set_active_scenario
from data.vehicles import BY_ID
from calculations.calculations import (
    calculate_tco, 
    calculate_scenario_comparison,
    calculate_breakeven_analysis,
    compare_vehicle_pairs
)


def test_basic_tco_calculation():
    """Test basic TCO calculation with default scenario."""
    print("=== Testing Basic TCO Calculation ===")
    
    # Get a BEV and diesel pair
    bev = BY_ID['BEV001']
    diesel = BY_ID['DSL001']
    
    # Calculate TCO with default scenario
    bev_tco = calculate_tco(bev)
    diesel_tco = calculate_tco(diesel)
    
    print(f"\nBEV ({bev.model_name}):")
    print(f"  Total Cost: ${bev_tco.total_cost:,.0f}")
    print(f"  Annual Cost: ${bev_tco.annual_cost:,.0f}")
    print(f"  Cost per km: ${bev_tco.cost_per_km:.3f}")
    print(f"  Scenario: {bev_tco.scenario_name}")
    
    print(f"\nDiesel ({diesel.model_name}):")
    print(f"  Total Cost: ${diesel_tco.total_cost:,.0f}")
    print(f"  Annual Cost: ${diesel_tco.annual_cost:,.0f}")
    print(f"  Cost per km: ${diesel_tco.cost_per_km:.3f}")
    print(f"  Scenario: {diesel_tco.scenario_name}")
    
    print(f"\nBEV Premium: ${bev_tco.total_cost - diesel_tco.total_cost:,.0f}")


def test_scenario_comparison():
    """Test TCO calculation across different scenarios."""
    print("\n\n=== Testing Scenario Comparison ===")
    
    vehicle_id = 'BEV001'
    scenarios = list(SCENARIOS.values())
    
    results = calculate_scenario_comparison(vehicle_id, scenarios)
    
    print(f"\nTCO for {BY_ID[vehicle_id].model_name} across scenarios:")
    print("-" * 60)
    print(f"{'Scenario':<25} {'Total TCO':<15} {'Annual Cost':<15} {'$/km':<10}")
    print("-" * 60)
    
    for scenario_name, tco in results.items():
        print(f"{scenario_name:<25} ${tco.total_cost:<14,.0f} ${tco.annual_cost:<14,.0f} ${tco.cost_per_km:<9.3f}")


def test_breakeven_analysis():
    """Test breakeven analysis across scenarios."""
    print("\n\n=== Testing Breakeven Analysis ===")
    
    bev_id = 'BEV001'
    diesel_id = 'DSL001'
    scenarios = list(SCENARIOS.values())
    
    results = calculate_breakeven_analysis(bev_id, diesel_id, scenarios)
    
    print(f"\nBEV vs Diesel cost difference across scenarios:")
    print(f"(Positive = BEV more expensive, Negative = BEV cheaper)")
    print("-" * 50)
    
    for scenario_name, difference in results.items():
        status = "BEV more expensive" if difference > 0 else "BEV cheaper"
        print(f"{scenario_name:<25} ${abs(difference):>10,.0f} ({status})")


def test_carbon_pricing():
    """Test carbon pricing impact."""
    print("\n\n=== Testing Carbon Pricing Impact ===")
    
    # Create a custom scenario with carbon pricing
    from data.scenarios import create_custom_scenario
    
    carbon_scenario = create_custom_scenario(
        name='Carbon Tax',
        description='Baseline with $50/tonne carbon tax',
        diesel_price_trajectory=SCENARIOS['baseline'].diesel_price_trajectory,
        electricity_price_trajectory=SCENARIOS['baseline'].electricity_price_trajectory,
        battery_price_trajectory=SCENARIOS['baseline'].battery_price_trajectory,
        carbon_price_trajectory=[50] * 15,  # $50/tonne for all years
        bev_efficiency_improvement=SCENARIOS['baseline'].bev_efficiency_improvement,
        diesel_efficiency_improvement=SCENARIOS['baseline'].diesel_efficiency_improvement,
    )
    
    # Compare diesel vehicle with and without carbon pricing
    diesel = BY_ID['DSL001']
    
    baseline_tco = calculate_tco(diesel, SCENARIOS['baseline'])
    carbon_tco = calculate_tco(diesel, carbon_scenario)
    
    print(f"\nDiesel vehicle ({diesel.model_name}):")
    print(f"  TCO without carbon tax: ${baseline_tco.total_cost:,.0f}")
    print(f"  TCO with carbon tax:    ${carbon_tco.total_cost:,.0f}")
    print(f"  Carbon tax impact:      ${carbon_tco.carbon_cost:,.0f}")
    print(f"  Total cost increase:    ${carbon_tco.total_cost - baseline_tco.total_cost:,.0f}")


def test_all_vehicle_pairs():
    """Test all vehicle pairs with different scenarios."""
    print("\n\n=== Testing All Vehicle Pairs ===")
    
    # Compare baseline vs oil crisis
    print("\nBaseline Scenario:")
    baseline_comparisons = compare_vehicle_pairs(SCENARIOS['baseline'])
    
    print(f"{'BEV Model':<25} {'Diesel Model':<25} {'TCO Difference':<20}")
    print("-" * 70)
    
    for bev_tco, diesel_tco, difference in baseline_comparisons[:3]:  # Show first 3
        bev_name = BY_ID[bev_tco.vehicle_id].model_name
        diesel_name = BY_ID[diesel_tco.vehicle_id].model_name
        status = "BEV +" if difference > 0 else "BEV -"
        print(f"{bev_name:<25} {diesel_name:<25} {status}${abs(difference):,.0f}")
    
    print("\nOil Crisis Scenario:")
    crisis_comparisons = compare_vehicle_pairs(SCENARIOS['oil_crisis'])
    
    for bev_tco, diesel_tco, difference in crisis_comparisons[:3]:  # Show first 3
        bev_name = BY_ID[bev_tco.vehicle_id].model_name
        diesel_name = BY_ID[diesel_tco.vehicle_id].model_name
        status = "BEV +" if difference > 0 else "BEV -"
        print(f"{bev_name:<25} {diesel_name:<25} {status}${abs(difference):,.0f}")


if __name__ == "__main__":
    print("Testing Scenario Integration in TCO Calculations")
    print("=" * 70)
    
    test_basic_tco_calculation()
    test_scenario_comparison()
    test_breakeven_analysis()
    test_carbon_pricing()
    test_all_vehicle_pairs()
    
    print("\n\nAll tests completed successfully!") 