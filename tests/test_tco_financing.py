"""
Test TCO financing calculations to verify NPV is calculated correctly.

Tests various scenarios:
1. Same vehicle with outright vs financed purchase
2. Different financing terms
3. Different interest rates
4. Different down payment rates
5. Different vehicle prices
"""

import sys
sys.path.append('..')

from calculations import calculate_tco, vehicle_data
from data import constants as const
from data.vehicles import BY_ID
from data.scenarios import SCENARIOS
import numpy_financial as npf


def manual_npv_financed(msrp, stamp_duty, rebate, down_payment_rate, interest_rate, term_years, discount_rate):
    """Manually calculate NPV for a financed purchase."""
    initial_cost = msrp + stamp_duty - rebate
    down_payment = initial_cost * down_payment_rate
    loan_amount = initial_cost - down_payment
    
    # Monthly payment calculation
    monthly_rate = interest_rate / 12
    num_payments = term_years * 12
    monthly_payment = float(npf.pmt(monthly_rate, num_payments, -loan_amount))
    
    # NPV of payments
    npv_down_payment = down_payment  # Paid in year 0
    
    # Calculate NPV of monthly payments
    npv_monthly_payments = 0
    for month in range(1, num_payments + 1):
        year_fraction = month / 12
        discount_factor = (1 + discount_rate) ** year_fraction
        npv_monthly_payments += monthly_payment / discount_factor
    
    total_npv = npv_down_payment + npv_monthly_payments
    total_paid = down_payment + (monthly_payment * num_payments)
    financing_cost = total_paid - initial_cost
    
    return {
        'initial_cost': initial_cost,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'total_paid': total_paid,
        'financing_cost': financing_cost,
        'npv_of_payments': total_npv,
        'npv_of_financing_cost': total_npv - initial_cost
    }


def test_scenario(vehicle_id, purchase_method, scenario_name="baseline"):
    """Test a specific scenario and return key metrics."""
    vehicle = BY_ID[vehicle_id]
    scenario = SCENARIOS[scenario_name]
    
    # Get vehicle inputs
    inputs = vehicle_data.get_vehicle(vehicle_id, scenario, purchase_method)
    
    # Calculate TCO
    tco = calculate_tco(vehicle, scenario, purchase_method)
    
    print(f"\n{'='*60}")
    print(f"Vehicle: {vehicle.model_name} ({vehicle_id})")
    print(f"Purchase Method: {purchase_method}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*60}")
    
    print(f"\nVehicle Price: ${vehicle.msrp:,.2f}")
    print(f"Stamp Duty: ${inputs.stamp_duty:,.2f}")
    print(f"Rebate: ${inputs.rebate:,.2f}")
    print(f"Initial Cost: ${inputs.initial_cost:,.2f}")
    
    if purchase_method == 'financed':
        print(f"\nFinancing Details:")
        print(f"  Down Payment: ${inputs.down_payment:,.2f}")
        print(f"  Loan Amount: ${inputs.loan_amount:,.2f}")
        print(f"  Monthly Payment: ${inputs.monthly_payment:,.2f}")
        print(f"  Total Financing Cost: ${inputs.total_financing_cost:,.2f}")
        print(f"  Total Paid: ${inputs.down_payment + (inputs.monthly_payment * const.FINANCING_TERM * 12):,.2f}")
        
        # Manual NPV calculation
        manual_calc = manual_npv_financed(
            vehicle.msrp, 
            inputs.stamp_duty, 
            inputs.rebate,
            const.DOWN_PAYMENT_RATE,
            const.INTEREST_RATE,
            const.FINANCING_TERM,
            const.DISCOUNT_RATE
        )
        
        print(f"\nManual NPV Calculation:")
        print(f"  NPV of all payments: ${manual_calc['npv_of_payments']:,.2f}")
        print(f"  NPV of financing cost: ${manual_calc['npv_of_financing_cost']:,.2f}")
    
    print(f"\nTCO Results:")
    print(f"  Purchase Cost (upfront): ${tco.purchase_cost:,.2f}")
    print(f"  Financing Cost: ${tco.financing_cost:,.2f}")
    print(f"  Total Cost: ${tco.total_cost:,.2f}")
    print(f"  Annual Cost: ${tco.annual_cost:,.2f}")
    print(f"  Cost per km: ${tco.cost_per_km:.3f}")
    
    return tco, inputs


def compare_purchase_methods(vehicle_id):
    """Compare outright vs financed purchase for the same vehicle."""
    print(f"\n{'#'*80}")
    print(f"COMPARING PURCHASE METHODS FOR {vehicle_id}")
    print(f"{'#'*80}")
    
    tco_outright, inputs_outright = test_scenario(vehicle_id, 'outright')
    tco_financed, inputs_financed = test_scenario(vehicle_id, 'financed')
    
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"Total Cost Difference: ${tco_financed.total_cost - tco_outright.total_cost:,.2f}")
    print(f"This should equal the financing cost: ${tco_financed.financing_cost:,.2f}")
    print(f"Match: {abs((tco_financed.total_cost - tco_outright.total_cost) - tco_financed.financing_cost) < 0.01}")


def main():
    """Run comprehensive tests."""
    print("TCO FINANCING VERIFICATION TESTS")
    print("="*80)
    
    # Test 1: Compare purchase methods for different vehicle types
    print("\n1. Testing Different Vehicle Types")
    for vehicle_id in ['BEV001', 'DSL001', 'BEV006', 'DSL006']:
        compare_purchase_methods(vehicle_id)
    
    # Test 2: Manual verification of a specific case
    print(f"\n\n{'#'*80}")
    print("2. DETAILED MANUAL VERIFICATION")
    print(f"{'#'*80}")
    
    vehicle_id = 'BEV004'
    vehicle = BY_ID[vehicle_id]
    inputs = vehicle_data.get_vehicle(vehicle_id, SCENARIOS['baseline'], 'financed')
    
    print(f"\nVehicle: {vehicle.model_name}")
    print(f"MSRP: ${vehicle.msrp:,.2f}")
    print(f"Initial Cost: ${inputs.initial_cost:,.2f}")
    
    # Show the issue
    print(f"\n⚠️  POTENTIAL ISSUE:")
    print(f"The current implementation adds the full purchase cost (${inputs.initial_cost:,.2f})")
    print(f"as if it were paid upfront, then adds financing cost (${inputs.total_financing_cost:,.2f}).")
    print(f"But for NPV, we should discount the monthly payments over time.")
    
    # Calculate what the NPV should be
    manual_calc = manual_npv_financed(
        vehicle.msrp,
        inputs.stamp_duty,
        inputs.rebate,
        const.DOWN_PAYMENT_RATE,
        const.INTEREST_RATE,
        const.FINANCING_TERM,
        const.DISCOUNT_RATE
    )
    
    print(f"\nCorrect NPV approach:")
    print(f"  Down payment (Year 0): ${manual_calc['down_payment']:,.2f}")
    print(f"  NPV of monthly payments: ${manual_calc['npv_of_payments'] - manual_calc['down_payment']:,.2f}")
    print(f"  Total NPV of purchase: ${manual_calc['npv_of_payments']:,.2f}")
    print(f"  NPV financing premium: ${manual_calc['npv_of_financing_cost']:,.2f}")
    
    print(f"\nCurrent implementation:")
    print(f"  Uses full purchase cost: ${inputs.initial_cost:,.2f}")
    print(f"  Plus financing cost: ${inputs.total_financing_cost:,.2f}")
    print(f"  Total: ${inputs.initial_cost + inputs.total_financing_cost:,.2f}")
    
    print(f"\nDifference: ${(inputs.initial_cost + inputs.total_financing_cost) - manual_calc['npv_of_payments']:,.2f}")


if __name__ == "__main__":
    main() 