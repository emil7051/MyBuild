"""
Comprehensive test suite for TCO calculator.
Consolidates all tests with maximum coverage and minimal duplication.
"""

import pytest
import numpy as np
import numpy_financial as npf
from typing import List, Dict

from data.vehicles import VehicleModel, BY_ID, ALL_MODELS
from data.scenarios import EconomicScenario, SCENARIOS, create_custom_scenario
from data import constants as const
from calculations.inputs import VehicleInputs, vehicle_data
from calculations.calculations import (
    calculate_tco, 
    calculate_tco_from_inputs,
    compare_vehicle_pairs,
    calculate_scenario_comparison,
    calculate_breakeven_analysis
)
from calculations.financial import (
    calculate_stamp_duty, 
    calculate_rebate,
    FinancingCalculator,
    DepreciationCalculator
)
from calculations.operating import (
    FuelCostCalculator,
    MaintenanceCostCalculator,
    ChargingTimeCostCalculator
)
from calculations.utils import calculate_present_value, discount_to_present, calculate_npv_of_payments
from scripts.validation import DataValidator
from calculations.simulation import (
    MonteCarloSimulation, 
    UncertaintyParameter,
    SensitivityAnalysis
)


class TestFinancialCalculations:
    """Test financial calculation functions."""
    
    def test_stamp_duty_calculation(self):
        """Test stamp duty calculations."""
        msrp = 100000
        expected = msrp * const.STAMP_DUTY_RATE
        assert calculate_stamp_duty(msrp, is_bev=False) == expected
        
    def test_present_value_calculations(self):
        """Test present value and discounting calculations."""
        annual_amount = 10000
        years = 5
        discount_rate = 0.05
        
        # Test calculate_present_value
        expected_pv = sum(annual_amount / (1 + discount_rate) ** i for i in range(1, years + 1))
        calculated_pv = calculate_present_value(annual_amount, years, discount_rate)
        assert abs(calculated_pv - expected_pv) < 0.01
        
        # Test discount_to_present
        future_amount = 10000
        year = 5
        expected_discount = future_amount / (1 + discount_rate) ** (year - 1)
        calculated_discount = discount_to_present(future_amount, year, discount_rate)
        assert abs(calculated_discount - expected_discount) < 0.01
        
    def test_financing_calculator(self):
        """Test financing calculations."""
        calc = FinancingCalculator()
        initial_cost = 100000
        
        down_payment = calc.calculate_down_payment(initial_cost)
        assert down_payment == initial_cost * const.DOWN_PAYMENT_RATE
        
        loan_amount = calc.calculate_loan_amount(initial_cost, down_payment)
        assert loan_amount == initial_cost - down_payment
        
        interest_rate = 0.06
        monthly_payment = calc.calculate_monthly_payment(loan_amount, interest_rate)
        assert monthly_payment > 0
        assert monthly_payment < loan_amount
        
    def test_depreciation_calculator(self):
        """Test depreciation calculations."""
        initial_cost = 100000
        calc = DepreciationCalculator(initial_cost)
        
        year1_depreciation = calc.get_depreciation_year(1)
        assert year1_depreciation == initial_cost * const.DEPRECIATION_RATE_FIRST_YEAR
        
        year2_depreciation = calc.get_depreciation_year(2)
        remaining_value = initial_cost - year1_depreciation
        expected = remaining_value * const.DEPRECIATION_RATE_ONGOING
        assert abs(year2_depreciation - expected) < 0.01
        
    def test_residual_value_calculator(self):
        """Test residual value calculations."""
        initial_cost = 100000
        calc = DepreciationCalculator(initial_cost)
        
        # Test year 0 (should return initial cost)
        assert calc.get_residual_value(0) == initial_cost
        
        # Test year 1 residual value
        year1_residual = calc.get_residual_value(1)
        expected_year1 = initial_cost * (1 - const.DEPRECIATION_RATE_FIRST_YEAR)
        assert abs(year1_residual - expected_year1) < 0.01
        
        # Test year 15 residual value
        residual_15 = calc.get_residual_value(15)
        assert residual_15 > 0  # Should still have some value
        assert residual_15 < initial_cost * 0.2  # Should be significantly depreciated
        
        # Verify residual value = initial cost - total depreciation
        total_depreciation = sum(calc.get_depreciation_year(y) for y in range(1, 16))
        residual_calculated = initial_cost - total_depreciation
        assert abs(residual_15 - residual_calculated) < 0.01


class TestOperatingCalculations:
    """Test operating cost calculations."""
    
    def test_fuel_cost_calculations(self):
        """Test fuel cost calculations for BEV and Diesel."""
        # BEV test
        bev = BY_ID['BEV001']
        bev_calc = FuelCostCalculator(bev)
        bev_base_cost = bev_calc.get_annual_base_cost()
        assert bev_base_cost > 0
        
        year5_cost = bev_calc.get_fuel_cost_year(5)
        assert year5_cost > 0
        
        # Diesel test
        diesel = BY_ID['DSL001']
        diesel_calc = FuelCostCalculator(diesel)
        diesel_base_cost = diesel_calc.get_annual_base_cost()
        expected = diesel.litres_per_km * diesel.annual_kms * const.DIESEL_PRICE
        assert abs(diesel_base_cost - expected) < 0.01
        
    def test_maintenance_cost_calculator(self):
        """Test maintenance cost calculations."""
        vehicle = BY_ID['BEV001']
        calc = MaintenanceCostCalculator(vehicle)
        
        base_cost = calc.get_annual_base_cost()
        assert base_cost > 0
        
        year10_cost = calc.get_maintenance_cost_year(10)
        assert year10_cost >= base_cost  # Should increase with age
        
    def test_charging_time_cost(self):
        """Test charging time labour cost calculation."""
        bev = BY_ID['BEV001']
        calc = ChargingTimeCostCalculator(bev)
        annual_cost = calc.calculate_annual_charging_labour_cost()
        assert annual_cost > 0
        
        # Diesel should return zero
        diesel = BY_ID['DSL001']
        calc_diesel = ChargingTimeCostCalculator(diesel)
        assert calc_diesel.calculate_annual_charging_labour_cost() == 0


class TestVehicleInputs:
    """Test VehicleInputs calculations."""
    
    def test_vehicle_inputs_initialization(self):
        """Test VehicleInputs properly initializes all fields."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        assert inputs.stamp_duty >= 0
        assert inputs.initial_cost > 0
        assert inputs.annual_fuel_cost_base > 0
        assert inputs.annual_maintenance_cost > 0
        assert inputs.annual_insurance_cost > 0
        
    def test_financing_vs_outright(self):
        """Test different purchase methods."""
        vehicle = BY_ID['BEV001']
        
        financed = VehicleInputs(vehicle, purchase_method='financed')
        outright = VehicleInputs(vehicle, purchase_method='outright')
        
        assert financed.total_financing_cost > 0
        assert financed.monthly_payment > 0
        assert outright.total_financing_cost == 0
        assert outright.monthly_payment == 0
        
    def test_year_specific_methods(self):
        """Test year-specific calculation methods."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        for year in [1, 5, 8, 10]:
            fuel_cost = inputs.get_fuel_cost_year(year)
            battery_cost = inputs.get_battery_replacement_year(year)
            assert fuel_cost > 0
            # Battery replacement only happens in year 8 for BEVs
            if year == 8 and vehicle.drivetrain_type == 'BEV':
                assert battery_cost > 0
            else:
                assert battery_cost == 0
                
    def test_residual_value_method(self):
        """Test residual value calculation in VehicleInputs."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        # Test residual value at different years
        residual_0 = inputs.get_residual_value(0)
        assert residual_0 == inputs.initial_cost
        
        residual_15 = inputs.get_residual_value(const.VEHICLE_LIFE)
        assert residual_15 > 0
        assert residual_15 < inputs.initial_cost
        
        # Residual value should decrease over time
        residual_5 = inputs.get_residual_value(5)
        residual_10 = inputs.get_residual_value(10)
        assert residual_5 > residual_10 > residual_15


class TestTCOCalculations:
    """Test TCO calculation functions."""
    
    def test_tco_calculation_basic(self):
        """Test basic TCO calculation."""
        vehicle = BY_ID['BEV001']
        tco = calculate_tco(vehicle)
        
        assert tco.total_cost > 0
        assert tco.annual_cost > 0
        assert tco.cost_per_km > 0
        assert tco.vehicle_id == vehicle.vehicle_id
        
    def test_tco_residual_value_approach(self):
        """Test that TCO properly uses residual value approach."""
        vehicle = BY_ID['BEV001']
        inputs = vehicle_data.get_vehicle(vehicle.vehicle_id)
        tco = calculate_tco(vehicle)
        
        # Verify residual_value field is populated and positive
        assert tco.residual_value > 0
        
        # Calculate expected residual value
        residual_future = inputs.get_residual_value(const.VEHICLE_LIFE)
        residual_pv = discount_to_present(residual_future, const.VEHICLE_LIFE)
        assert abs(tco.residual_value - residual_pv) < 0.01
        
        # Verify TCO calculation includes residual value as a credit
        # Re-calculate TCO components manually
        npv_purchase = inputs.initial_cost if inputs.purchase_method == 'outright' else (
            inputs.down_payment + calculate_npv_of_payments(
                inputs.monthly_payment, 
                const.FINANCING_TERM * 12, 
                const.DISCOUNT_RATE
            )
        )
        
        # Calculate PV of fixed annual costs
        insurance_pv = calculate_present_value(inputs.annual_insurance_cost, const.VEHICLE_LIFE)
        registration_pv = calculate_present_value(inputs.vehicle.annual_registration, const.VEHICLE_LIFE)
        
        # Sum all cost components (all values from TCO are already in present value)
        costs_without_residual = (
            npv_purchase +
            tco.fuel_cost +  # Already NPV
            tco.maintenance_cost +  # Already NPV
            insurance_pv +  # Calculate PV
            registration_pv +  # Calculate PV
            tco.battery_replacement_cost +  # Already NPV
            tco.carbon_cost +  # Already NPV
            tco.charging_labour_cost +  # Already NPV
            tco.payload_penalty_cost  # Already NPV
        )
        
        # The actual TCO should be approximately costs minus residual value
        # (allowing for rounding and other minor differences)
        expected_tco = costs_without_residual - residual_pv
        assert abs(tco.total_cost - expected_tco) / tco.total_cost < 0.01  # Within 1%
        
    def test_bev_vs_diesel_comparison(self):
        """Test BEV vs Diesel TCO comparison."""
        bev = BY_ID['BEV001']
        diesel = BY_ID['DSL001']
        
        bev_tco = calculate_tco(bev)
        diesel_tco = calculate_tco(diesel)
        
        assert bev_tco.total_cost > 0
        assert diesel_tco.total_cost > 0
        assert bev_tco.fuel_cost != diesel_tco.fuel_cost
        assert bev_tco.purchase_cost > diesel_tco.purchase_cost  # BEVs typically more expensive upfront
        
    def test_purchase_method_comparison(self):
        """Test financed vs outright purchase."""
        vehicle = BY_ID['BEV001']
        
        tco_financed = calculate_tco(vehicle, purchase_method='financed')
        tco_outright = calculate_tco(vehicle, purchase_method='outright')
        
        assert tco_financed.financing_cost > 0
        assert tco_outright.financing_cost == 0
        assert tco_financed.total_cost > tco_outright.total_cost  # Financing adds cost
        
    def test_scenario_impact(self):
        """Test that scenarios affect TCO calculations."""
        vehicle = BY_ID['BEV001']
        
        baseline_tco = calculate_tco(vehicle, SCENARIOS['baseline'])
        tech_breakthrough_tco = calculate_tco(vehicle, SCENARIOS['technology_breakthrough'])
        
        assert tech_breakthrough_tco.total_cost != baseline_tco.total_cost
        
    def test_scenario_comparison(self):
        """Test scenario comparison function."""
        vehicle_id = 'BEV001'
        scenarios = list(SCENARIOS.values())[:3]  # Test with first 3 scenarios
        
        results = calculate_scenario_comparison(vehicle_id, scenarios)
        
        assert len(results) == len(scenarios)
        for scenario_name, tco in results.items():
            assert tco.total_cost > 0
            assert tco.scenario_name == scenario_name
            
    def test_breakeven_analysis(self):
        """Test breakeven analysis across scenarios."""
        bev_id = 'BEV001'
        diesel_id = 'DSL001'
        scenarios = list(SCENARIOS.values())[:3]
        
        results = calculate_breakeven_analysis(bev_id, diesel_id, scenarios)
        
        assert len(results) == len(scenarios)
        for scenario_name, difference in results.items():
            assert isinstance(difference, (int, float))
            
    def test_carbon_pricing_impact(self):
        """Test carbon pricing impact on TCO."""
        carbon_scenario = create_custom_scenario(
            name='Carbon Tax Test',
            description='Test with carbon tax',
            diesel_price_trajectory=SCENARIOS['baseline'].diesel_price_trajectory,
            electricity_price_trajectory=SCENARIOS['baseline'].electricity_price_trajectory,
            battery_price_trajectory=SCENARIOS['baseline'].battery_price_trajectory,
            carbon_price_trajectory=[50] * 15,  # $50/tonne
            bev_efficiency_improvement=SCENARIOS['baseline'].bev_efficiency_improvement,
            diesel_efficiency_improvement=SCENARIOS['baseline'].diesel_efficiency_improvement,
        )
        
        diesel = BY_ID['DSL001']
        baseline_tco = calculate_tco(diesel, SCENARIOS['baseline'])
        carbon_tco = calculate_tco(diesel, carbon_scenario)
        
        assert carbon_tco.carbon_cost > 0
        assert carbon_tco.total_cost > baseline_tco.total_cost
        
    def test_all_vehicle_pairs(self):
        """Test that all vehicle pairs can be calculated."""
        comparisons = compare_vehicle_pairs()
        
        assert len(comparisons) > 0
        
        for bev_tco, diesel_tco, difference in comparisons:
            assert bev_tco.total_cost > 0
            assert diesel_tco.total_cost > 0
            assert difference == bev_tco.total_cost - diesel_tco.total_cost


class TestNPVFinancing:
    """Test NPV calculations for financing scenarios."""
    
    def calculate_manual_npv(self, initial_cost, down_payment_rate, interest_rate, 
                           term_years, discount_rate):
        """Helper to manually calculate NPV for verification."""
        down_payment = initial_cost * down_payment_rate
        loan_amount = initial_cost - down_payment
        
        if loan_amount > 0:
            monthly_rate = interest_rate / 12
            num_payments = term_years * 12
            monthly_payment = float(npf.pmt(monthly_rate, num_payments, -loan_amount))
            
            npv_payments = down_payment  # Year 0
            
            # Use the utility function for NPV of monthly payments
            npv_monthly_payments = calculate_npv_of_payments(monthly_payment, num_payments, discount_rate)
            npv_payments += npv_monthly_payments
            
            total_paid = down_payment + (monthly_payment * num_payments)
            financing_cost = total_paid - initial_cost
            npv_financing_cost = npv_payments - initial_cost
        else:
            npv_payments = initial_cost
            financing_cost = 0
            npv_financing_cost = 0
        
        return {
            'npv_payments': npv_payments,
            'financing_cost': financing_cost,
            'npv_financing_cost': npv_financing_cost
        }
        
    def test_npv_calculation_standard(self):
        """Test standard NPV calculation."""
        vehicle = BY_ID['BEV001']
        inputs_financed = vehicle_data.get_vehicle(vehicle.vehicle_id, SCENARIOS['baseline'], 'financed')
        inputs_outright = vehicle_data.get_vehicle(vehicle.vehicle_id, SCENARIOS['baseline'], 'outright')
        
        tco_financed = calculate_tco(vehicle, SCENARIOS['baseline'], 'financed')
        tco_outright = calculate_tco(vehicle, SCENARIOS['baseline'], 'outright')
        
        manual = self.calculate_manual_npv(
            inputs_financed.initial_cost,
            const.DOWN_PAYMENT_RATE,
            const.INTEREST_RATE,
            const.FINANCING_TERM,
            const.DISCOUNT_RATE
        )
        
        # The difference in TCO should match the NPV of financing cost
        tco_difference = tco_financed.total_cost - tco_outright.total_cost
        assert abs(tco_difference - manual['npv_financing_cost']) < 1.0
        
    def test_edge_cases(self):
        """Test edge cases for NPV calculation."""
        vehicle = BY_ID['BEV001']
        
        # Test with 100% down payment (effectively outright purchase)
        orig_down_payment = const.DOWN_PAYMENT_RATE
        const.DOWN_PAYMENT_RATE = 1.0
        
        try:
            vehicle_data._inputs_cache.clear()
            vehicle_data._initialise_all_vehicles()
            
            inputs = vehicle_data.get_vehicle(vehicle.vehicle_id, SCENARIOS['baseline'], 'financed')
            assert inputs.loan_amount == 0
            assert inputs.monthly_payment == 0
            assert inputs.total_financing_cost == 0
        finally:
            const.DOWN_PAYMENT_RATE = orig_down_payment
            vehicle_data._inputs_cache.clear()
            vehicle_data._initialise_all_vehicles()


class TestDataValidation:
    """Test data validation functions."""
    
    def test_vehicle_validation(self):
        """Test vehicle data validation."""
        invalid_vehicle = VehicleModel(
            vehicle_id='TEST001',
            comparison_pair='NONEXISTENT',
            weight_class='Light Rigid',
            drivetrain_type='BEV',
            model_name='Test Vehicle',
            payload=50,  # Too high for light rigid
            msrp=-100000,  # Negative price
            range_km=200,
            battery_capacity_kwh=100,
            kwh_per_km=0.2,  # Inconsistent with range
            litres_per_km=0,
            battery_replacement_per_kw=130,
            maintenance_cost_per_km=0.05,
            annual_registration=653,
            annual_kms=0,  # Zero kms
            noise_pollution_per_km=0.004
        )
        
        issues = DataValidator.validate_vehicle(invalid_vehicle)
        assert len(issues) > 0
        assert any('MSRP must be positive' in issue for issue in issues)
        assert any('Annual kms must be positive' in issue for issue in issues)
        assert any('Payload' in issue for issue in issues)
        
    def test_scenario_validation(self):
        """Test scenario validation."""
        invalid_scenario = EconomicScenario(
            name='Invalid',
            description='Test invalid scenario',
            diesel_price_trajectory=[1.0, -0.5],  # Negative price
            electricity_price_trajectory=[1.0],  # Too short
            battery_price_trajectory=[]  # Empty
        )
        
        issues = DataValidator.validate_scenario(invalid_scenario)
        assert len(issues) > 0
        
    def test_comparison_pairs_validation(self):
        """Test comparison pairs validation."""
        issues = DataValidator.validate_comparison_pairs()
        # Should validate successfully if data is properly configured
        # Any issues would indicate data configuration problems
        
    def test_validate_all(self):
        """Test comprehensive validation."""
        all_issues = DataValidator.validate_all()
        
        assert isinstance(all_issues, dict)
        assert 'vehicles' in all_issues
        assert 'scenarios' in all_issues
        assert 'comparison_pairs' in all_issues


class TestMonteCarloSimulation:
    """Test Monte Carlo simulation and sensitivity analysis."""
    
    def test_uncertainty_parameter_sampling(self):
        """Test uncertainty parameter sampling."""
        # Normal distribution
        param_normal = UncertaintyParameter(
            name='test_normal',
            distribution='normal',
            base_value=100,
            std_dev=10
        )
        samples = [param_normal.sample() for _ in range(1000)]
        assert 70 < np.mean(samples) < 130
        
        # Uniform distribution
        param_uniform = UncertaintyParameter(
            name='test_uniform',
            distribution='uniform',
            base_value=100,
            min_value=50,
            max_value=150
        )
        samples_uniform = [param_uniform.sample() for _ in range(1000)]
        assert 50 <= min(samples_uniform) <= 150
        assert 50 <= max(samples_uniform) <= 150
        
        # Triangular distribution
        param_triangular = UncertaintyParameter(
            name='test_triangular',
            distribution='triangular',
            base_value=100,
            min_value=50,
            max_value=150,
            mode_value=100
        )
        samples_triangular = [param_triangular.sample() for _ in range(100)]
        assert 50 <= min(samples_triangular) <= 150
        
    def test_monte_carlo_simulation_run(self):
        """Test Monte Carlo simulation execution."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        simulation = MonteCarloSimulation(inputs)
        results = simulation.run(iterations=100, seed=42)
        
        assert results.iterations == 100
        assert len(results.tco_values) == 100
        assert results.mean > 0
        assert results.std_dev > 0
        assert results.min_value < results.max_value
        assert len(results.percentiles) > 0
        assert results.confidence_interval_95[0] < results.confidence_interval_95[1]
        
    def test_simulation_comparison(self):
        """Test Monte Carlo comparison between vehicles."""
        bev = BY_ID['BEV001']
        diesel = BY_ID[bev.comparison_pair]
        
        bev_inputs = VehicleInputs(bev)
        diesel_inputs = VehicleInputs(diesel)
        
        simulation = MonteCarloSimulation(bev_inputs)
        bev_results, diesel_results, differences = simulation.compare_uncertainty(
            diesel_inputs, 
            iterations=100
        )
        
        assert bev_results.iterations == 100
        assert diesel_results.iterations == 100
        assert len(differences) == 100
        assert abs(np.mean(differences) - (bev_results.mean - diesel_results.mean)) < 1.0
        
    def test_sensitivity_analysis(self):
        """Test sensitivity analysis."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        sensitivity = SensitivityAnalysis(inputs)
        
        # Test electricity price sensitivity for BEV
        results = sensitivity.analyse_parameter(
            'electricity_price',
            [0.8, 1.0, 1.2],
            parameter_type='multiplier'
        )
        
        assert len(results) == 3
        assert results[0][2] < 0  # Lower price = negative percent change
        assert results[2][2] > 0  # Higher price = positive percent change
        
    def test_tornado_analysis(self):
        """Test tornado diagram analysis."""
        vehicle = BY_ID['BEV001']
        inputs = VehicleInputs(vehicle)
        
        sensitivity = SensitivityAnalysis(inputs)
        
        parameters = {
            'electricity_price': (0.8, 1.2),
            'maintenance_cost': (0.9, 1.1),
            'interest_rate': (0.9, 1.1)
        }
        
        results = sensitivity.tornado_analysis(parameters)
        
        assert len(results) == len(parameters)
        # Results should be sorted by impact range (largest first)
        impact_ranges = [r[3] for r in results]
        assert impact_ranges == sorted(impact_ranges, reverse=True)


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_bev_diesel_comparison(self):
        """Test complete BEV vs Diesel comparison workflow."""
        bev = BY_ID['BEV001']
        diesel = BY_ID[bev.comparison_pair]
        
        # Calculate TCOs
        bev_tco = calculate_tco(bev)
        diesel_tco = calculate_tco(diesel)
        
        # Run uncertainty analysis
        bev_inputs = vehicle_data.get_vehicle(bev.vehicle_id)
        diesel_inputs = vehicle_data.get_vehicle(diesel.vehicle_id)
        
        simulation = MonteCarloSimulation(bev_inputs)
        bev_results, diesel_results, differences = simulation.compare_uncertainty(
            diesel_inputs, 
            iterations=100
        )
        
        # Results should be consistent
        assert abs(bev_results.mean - bev_tco.total_cost) / bev_tco.total_cost < 0.2
        assert abs(diesel_results.mean - diesel_tco.total_cost) / diesel_tco.total_cost < 0.2
        
    def test_scenario_workflow(self):
        """Test complete scenario analysis workflow."""
        vehicle_id = 'BEV001'
        
        # Compare across scenarios
        scenario_results = calculate_scenario_comparison(
            vehicle_id, 
            list(SCENARIOS.values())[:3]
        )
        
        # Calculate breakeven for each scenario
        diesel_id = BY_ID[vehicle_id].comparison_pair
        breakeven_results = calculate_breakeven_analysis(
            vehicle_id, 
            diesel_id, 
            list(SCENARIOS.values())[:3]
        )
        
        assert len(scenario_results) == 3
        assert len(breakeven_results) == 3
        
        # Results should be internally consistent
        for scenario_name in scenario_results:
            assert scenario_name in breakeven_results


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 