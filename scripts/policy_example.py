"""
Example script demonstrating how to use the policy incentive system.
"""

from data import policies
from calculations.inputs import vehicle_data


def print_policy_status():
    """Print the current status of all policies."""
    print("\n=== Current Policy Status ===")
    for key, policy in policies.POLICIES.items():
        status = "ENABLED" if policy.enabled else "DISABLED"
        print(f"{policy.name}: {status}")
        if policy.enabled:
            # Print key parameters for enabled policies
            if hasattr(policy, 'amount'):
                print(f"  - Amount: ${policy.amount:,.0f}")
            if hasattr(policy, 'percentage'):
                print(f"  - Percentage: {policy.percentage:.1%}")
            if hasattr(policy, 'exemption_percentage'):
                print(f"  - Exemption: {policy.exemption_percentage:.0%}")
            if hasattr(policy, 'annual_charge'):
                print(f"  - Annual charge: ${policy.annual_charge:,.0f}")
            if hasattr(policy, 'price_per_tonne'):
                print(f"  - Price per tonne: ${policy.price_per_tonne:.0f}")
            if hasattr(policy, 'rate_reduction'):
                print(f"  - Rate reduction: {policy.rate_reduction:.1%}")
    print()


def compare_vehicle_costs(vehicle_id: str):
    """Compare costs for a vehicle with and without policies."""
    vehicle = vehicle_data.get_vehicle(vehicle_id)
    
    print(f"\n=== Cost Analysis for {vehicle.vehicle.model_name} ===")
    print(f"MSRP: ${vehicle.vehicle.msrp:,.0f}")
    print(f"Drivetrain: {vehicle.vehicle.drivetrain_type}")
    
    # Current costs (with active policies)
    print(f"\nWith Active Policies:")
    print(f"  Stamp Duty: ${vehicle.stamp_duty:,.0f}")
    print(f"  Rebate: ${vehicle.rebate:,.0f}")
    print(f"  Initial Cost: ${vehicle.initial_cost:,.0f}")
    print(f"  Financing Cost: ${vehicle.total_financing_cost:,.0f}")
    
    # Calculate what costs would be without policies
    if vehicle.vehicle.drivetrain_type == 'BEV':
        base_stamp_duty = vehicle.vehicle.msrp * 0.03  # Base 3% stamp duty
        base_initial_cost = vehicle.vehicle.msrp + base_stamp_duty
        base_financing = base_initial_cost - base_initial_cost * 0.20  # 20% down payment
        
        print(f"\nWithout Policies:")
        print(f"  Stamp Duty: ${base_stamp_duty:,.0f}")
        print(f"  Rebate: $0")
        print(f"  Initial Cost: ${base_initial_cost:,.0f}")
        
        print(f"\nPolicy Impact:")
        print(f"  Stamp Duty Savings: ${base_stamp_duty - vehicle.stamp_duty:,.0f}")
        print(f"  Total Upfront Savings: ${base_initial_cost - vehicle.initial_cost:,.0f}")


def main():
    """Demonstrate different policy scenarios."""
    
    # Scenario 1: No policies
    print("\n" + "="*60)
    print("SCENARIO 1: No Policy Incentives")
    print("="*60)
    policies.disable_all_policies()
    print_policy_status()
    
    # Recalculate vehicle data with no policies
    vehicle_data._initialise_all_vehicles()
    compare_vehicle_costs("BEV004")  # Volvo FL Electric
    
    # Scenario 2: Standard incentives
    print("\n" + "="*60)
    print("SCENARIO 2: Standard BEV Incentives")
    print("="*60)
    policies.enable_standard_incentives()
    print_policy_status()
    
    # Recalculate vehicle data with standard policies
    vehicle_data._initialise_all_vehicles()
    compare_vehicle_costs("BEV004")  # Volvo FL Electric
    
    # Scenario 3: Aggressive incentives
    print("\n" + "="*60)
    print("SCENARIO 3: Aggressive Policy Mix")
    print("="*60)
    policies.enable_aggressive_incentives()
    print_policy_status()
    
    # Recalculate vehicle data with aggressive policies
    vehicle_data._initialise_all_vehicles()
    compare_vehicle_costs("BEV004")  # Volvo FL Electric
    
    # Scenario 4: Custom policy mix
    print("\n" + "="*60)
    print("SCENARIO 4: Custom Policy Mix")
    print("="*60)
    policies.disable_all_policies()
    
    # Enable specific policies with custom values
    policies.POLICIES['percentage_rebate'].enabled = True
    policies.POLICIES['percentage_rebate'].percentage = 0.10  # 10% rebate
    policies.POLICIES['percentage_rebate'].max_amount = 30000  # Capped at $30k
    
    policies.POLICIES['stamp_duty_exemption'].enabled = True
    policies.POLICIES['stamp_duty_exemption'].exemption_percentage = 0.5  # 50% exemption
    
    policies.POLICIES['carbon_pricing'].enabled = True
    policies.POLICIES['carbon_pricing'].price_per_tonne = 25  # $25 per tonne
    
    print_policy_status()
    
    # Recalculate vehicle data with custom policies
    vehicle_data._initialise_all_vehicles()
    compare_vehicle_costs("BEV004")  # Volvo FL Electric
    compare_vehicle_costs("DSL004")  # Volvo FE Diesel (comparison pair)


if __name__ == "__main__":
    main() 