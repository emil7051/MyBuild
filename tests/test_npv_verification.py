"""
Comprehensive NPV verification for TCO calculations.

Tests various financing scenarios to ensure NPV is calculated correctly.
"""

import sys
sys.path.append('..')

from calculations import calculate_tco, vehicle_data
from data import constants as const
from data.vehicles import BY_ID
from data.scenarios import SCENARIOS, EconomicScenario
import numpy_financial as npf
from dataclasses import replace


def create_custom_financing_scenario(
    down_payment_rate: float,
    interest_rate: float,
    financing_term: int,
    discount_rate: float
):
    """Create a custom financing scenario by modifying constants."""
    # Save original values
    orig_down_payment = const.DOWN_PAYMENT_RATE
    orig_interest = const.INTEREST_RATE
    orig_term = const.FINANCING_TERM
    orig_discount = const.DISCOUNT_RATE
    
    # Set new values
    const.DOWN_PAYMENT_RATE = down_payment_rate
    const.INTEREST_RATE = interest_rate
    const.FINANCING_TERM = financing_term
    const.DISCOUNT_RATE = discount_rate
    
    return orig_down_payment, orig_interest, orig_term, orig_discount


def restore_constants(orig_values):
    """Restore original constant values."""
    const.DOWN_PAYMENT_RATE = orig_values[0]
    const.INTEREST_RATE = orig_values[1]
    const.FINANCING_TERM = orig_values[2]
    const.DISCOUNT_RATE = orig_values[3]


def calculate_manual_npv(
    initial_cost: float,
    down_payment_rate: float,
    interest_rate: float,
    term_years: int,
    discount_rate: float
) -> dict:
    """Manually calculate NPV for verification."""
    down_payment = initial_cost * down_payment_rate
    loan_amount = initial_cost - down_payment
    
    if loan_amount > 0:
        monthly_rate = interest_rate / 12
        num_payments = term_years * 12
        monthly_payment = float(npf.pmt(monthly_rate, num_payments, -loan_amount))
        
        # NPV calculation
        npv_payments = down_payment  # Year 0
        
        for month in range(1, num_payments + 1):
            year_fraction = month / 12.0
            discount_factor = (1 + discount_rate) ** year_fraction
            npv_payments += monthly_payment / discount_factor
        
        total_paid = down_payment + (monthly_payment * num_payments)
        financing_cost = total_paid - initial_cost
        npv_financing_cost = npv_payments - initial_cost
    else:
        # All cash purchase
        npv_payments = initial_cost
        total_paid = initial_cost
        financing_cost = 0
        npv_financing_cost = 0
        monthly_payment = 0
    
    return {
        'initial_cost': initial_cost,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'total_paid': total_paid,
        'financing_cost': financing_cost,
        'npv_payments': npv_payments,
        'npv_financing_cost': npv_financing_cost
    }


def test_financing_scenario(
    vehicle_id: str,
    scenario_name: str,
    down_payment_rate: float,
    interest_rate: float,
    financing_term: int,
    discount_rate: float
):
    """Test a specific financing scenario."""
    # Set up custom financing parameters
    orig_values = create_custom_financing_scenario(
        down_payment_rate, interest_rate, financing_term, discount_rate
    )
    
    try:
        vehicle = BY_ID[vehicle_id]
        scenario = SCENARIOS[scenario_name]
        
        # Clear the cache to force recalculation
        vehicle_data._inputs_cache.clear()
        vehicle_data._initialise_all_vehicles()
        
        # Calculate TCO
        inputs_financed = vehicle_data.get_vehicle(vehicle_id, scenario, 'financed')
        inputs_outright = vehicle_data.get_vehicle(vehicle_id, scenario, 'outright')
        
        tco_financed = calculate_tco(vehicle, scenario, 'financed')
        tco_outright = calculate_tco(vehicle, scenario, 'outright')
        
        # Manual calculation
        manual = calculate_manual_npv(
            inputs_financed.initial_cost,
            down_payment_rate,
            interest_rate,
            financing_term,
            discount_rate
        )
        
        print(f"\n{'='*70}")
        print(f"Scenario: {down_payment_rate:.0%} down, {interest_rate:.1%} rate, {financing_term}yr term, {discount_rate:.1%} discount")
        print(f"Vehicle: {vehicle.model_name} (${vehicle.msrp:,.0f})")
        print(f"{'='*70}")
        
        print(f"\nPurchase Details:")
        print(f"  Initial Cost: ${inputs_financed.initial_cost:,.2f}")
        print(f"  Down Payment: ${manual['down_payment']:,.2f}")
        print(f"  Loan Amount: ${manual['loan_amount']:,.2f}")
        print(f"  Monthly Payment: ${manual['monthly_payment']:,.2f}")
        
        print(f"\nFinancing Analysis:")
        print(f"  Total Paid: ${manual['total_paid']:,.2f}")
        print(f"  Financing Cost: ${manual['financing_cost']:,.2f}")
        print(f"  NPV of Payments: ${manual['npv_payments']:,.2f}")
        print(f"  NPV Premium vs Cash: ${manual['npv_financing_cost']:,.2f}")
        
        print(f"\nTCO Comparison:")
        print(f"  Outright TCO: ${tco_outright.total_cost:,.2f}")
        print(f"  Financed TCO: ${tco_financed.total_cost:,.2f}")
        print(f"  TCO Difference: ${tco_financed.total_cost - tco_outright.total_cost:,.2f}")
        print(f"  Expected (NPV premium): ${manual['npv_financing_cost']:,.2f}")
        
        # Verification
        difference = (tco_financed.total_cost - tco_outright.total_cost) - manual['npv_financing_cost']
        print(f"\n✓ Verification: {'PASS' if abs(difference) < 1.0 else 'FAIL'} (diff: ${difference:.2f})")
        
        return abs(difference) < 1.0
        
    finally:
        restore_constants(orig_values)
        # Clear cache again
        vehicle_data._inputs_cache.clear()
        vehicle_data._initialise_all_vehicles()


def run_comprehensive_tests():
    """Run a comprehensive set of financing scenarios."""
    print("NPV VERIFICATION FOR TCO FINANCING")
    print("="*70)
    
    test_scenarios = [
        # (vehicle_id, down_payment_rate, interest_rate, term_years, discount_rate)
        ('BEV001', 0.20, 0.06, 5, 0.05),    # Standard scenario
        ('BEV001', 0.10, 0.06, 5, 0.05),    # Lower down payment
        ('BEV001', 0.50, 0.06, 5, 0.05),    # Higher down payment
        ('BEV001', 0.20, 0.03, 5, 0.05),    # Lower interest rate
        ('BEV001', 0.20, 0.09, 5, 0.05),    # Higher interest rate
        ('BEV001', 0.20, 0.06, 3, 0.05),    # Shorter term
        ('BEV001', 0.20, 0.06, 7, 0.05),    # Longer term
        ('BEV001', 0.20, 0.06, 5, 0.03),    # Lower discount rate
        ('BEV001', 0.20, 0.06, 5, 0.08),    # Higher discount rate
        ('DSL006', 0.20, 0.06, 5, 0.05),    # Different vehicle (diesel truck)
        ('BEV006', 0.20, 0.06, 5, 0.05),    # Expensive BEV truck
        ('BEV001', 1.00, 0.00, 1, 0.05),    # All cash (100% down payment)
    ]
    
    passed = 0
    failed = 0
    
    for vehicle_id, down_rate, int_rate, term, disc_rate in test_scenarios:
        success = test_financing_scenario(
            vehicle_id, 'baseline', down_rate, int_rate, term, disc_rate
        )
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print(f"{'='*70}")


def test_edge_cases():
    """Test edge cases and special scenarios."""
    print("\n\nEDGE CASE TESTING")
    print("="*70)
    
    # Test with very high discount rate
    print("\n1. Very High Discount Rate (20%)")
    test_financing_scenario('BEV001', 'baseline', 0.20, 0.06, 5, 0.20)
    
    # Test with zero interest rate
    print("\n2. Zero Interest Rate")
    test_financing_scenario('BEV001', 'baseline', 0.20, 0.00, 5, 0.05)
    
    # Test with very small down payment
    print("\n3. Minimal Down Payment (5%)")
    test_financing_scenario('BEV001', 'baseline', 0.05, 0.06, 5, 0.05)


if __name__ == "__main__":
    run_comprehensive_tests()
    test_edge_cases() 