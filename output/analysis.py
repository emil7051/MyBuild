"""
Core analysis functions for TCO reporting.
"""

import numpy as np
import numpy_financial as npf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import copy

from calculations.inputs import VehicleInputs, vehicle_data
from calculations.calculations import calculate_tco_from_inputs, TCOResult
from calculations.utils import discount_to_present
from data import constants as const
from data import policies
from data.scenarios import EconomicScenario
from data.vehicles import BY_ID


@dataclass
class PaybackAnalysis:
    """Results from payback period analysis."""
    bev_id: str
    diesel_id: str
    payback_years: float
    cumulative_bev_costs: List[float]
    cumulative_diesel_costs: List[float]
    annual_savings: List[float]
    breakeven_achieved: bool
    total_savings_15yr: float
    npv_savings: float


@dataclass
class PolicyImpactAnalysis:
    """Analysis of policy impact on TCO."""
    policy_combination: Dict[str, float]
    avg_tco_difference: float
    vehicles_becoming_viable: int
    total_policy_cost: float
    cost_effectiveness: float  # $ policy cost per $ TCO reduction


@dataclass
class FleetTransitionAnalysis:
    """Fleet-wide transition analysis."""
    total_vehicles: int
    transition_schedule: Dict[int, List[str]]  # year -> vehicle IDs
    cumulative_investment: List[float]
    cumulative_savings: List[float]
    cumulative_emissions_reduction: List[float]
    average_payback: float


def calculate_payback_analysis(
    bev_inputs: VehicleInputs, 
    diesel_inputs: VehicleInputs
) -> PaybackAnalysis:
    """
    Calculate detailed payback period with year-by-year cumulative costs.
    
    Tracks actual cash flows rather than discounted values for payback calculation.
    """
    cumulative_bev_costs = []
    cumulative_diesel_costs = []
    annual_savings = []
    
    # Initial costs (year 0)
    if bev_inputs.purchase_method == 'outright':
        bev_cumulative = bev_inputs.initial_cost
    else:
        bev_cumulative = bev_inputs.down_payment
        
    if diesel_inputs.purchase_method == 'outright':
        diesel_cumulative = diesel_inputs.initial_cost
    else:
        diesel_cumulative = diesel_inputs.down_payment
    
    # Track year-by-year costs
    payback_year = None
    
    for year in range(1, const.VEHICLE_LIFE + 1):
        # Annual operating costs for BEV
        bev_annual = (
            bev_inputs.get_fuel_cost_year(year) +
            bev_inputs.get_maintenance_cost_year(year) +
            bev_inputs.annual_insurance_cost +
            bev_inputs.vehicle.annual_registration +
            bev_inputs.get_battery_replacement_year(year) +
            bev_inputs.get_charging_labour_cost_year(year) +
            bev_inputs.get_payload_penalty_year(year)
        )
        
        # Annual operating costs for Diesel
        diesel_annual = (
            diesel_inputs.get_fuel_cost_year(year) +
            diesel_inputs.get_maintenance_cost_year(year) +
            diesel_inputs.annual_insurance_cost +
            diesel_inputs.vehicle.annual_registration +
            diesel_inputs.get_carbon_cost_year(year)
        )
        
        # Add financing payments if applicable
        if bev_inputs.purchase_method == 'financed' and year <= const.FINANCING_TERM:
            bev_annual += bev_inputs.monthly_payment * const.MONTHS_IN_YEAR
            
        if diesel_inputs.purchase_method == 'financed' and year <= const.FINANCING_TERM:
            diesel_annual += diesel_inputs.monthly_payment * const.MONTHS_IN_YEAR
        
        # Update cumulative costs
        bev_cumulative += bev_annual
        diesel_cumulative += diesel_annual
        
        cumulative_bev_costs.append(bev_cumulative)
        cumulative_diesel_costs.append(diesel_cumulative)
        annual_savings.append(diesel_annual - bev_annual)
        
        # Check for payback
        if payback_year is None and diesel_cumulative > bev_cumulative:
            # Interpolate to find exact payback point
            if year == 1:
                payback_year = (bev_inputs.initial_cost - diesel_inputs.initial_cost) / annual_savings[0]
            else:
                prev_diff = cumulative_bev_costs[year-2] - cumulative_diesel_costs[year-2]
                curr_diff = bev_cumulative - diesel_cumulative
                payback_year = year - 1 + (prev_diff / (prev_diff - curr_diff))
    
    # Calculate NPV of savings
    npv_savings = 0
    for year, saving in enumerate(annual_savings, 1):
        npv_savings += discount_to_present(saving, year)
    
    return PaybackAnalysis(
        bev_id=bev_inputs.vehicle.vehicle_id,
        diesel_id=diesel_inputs.vehicle.vehicle_id,
        payback_years=payback_year if payback_year else float('inf'),
        cumulative_bev_costs=cumulative_bev_costs,
        cumulative_diesel_costs=cumulative_diesel_costs,
        annual_savings=annual_savings,
        breakeven_achieved=payback_year is not None,
        total_savings_15yr=cumulative_diesel_costs[-1] - cumulative_bev_costs[-1],
        npv_savings=npv_savings
    )


def analyse_policy_combinations(
    scenario: Optional[EconomicScenario] = None,
    purchase_method: str = 'financed'
) -> List[PolicyImpactAnalysis]:
    """
    Test combinations of policy levers and their impact.
    
    Returns list of PolicyImpactAnalysis objects sorted by cost effectiveness.
    """
    # Save current policy state
    original_policies = {}
    for key, policy in policies.POLICIES.items():
        original_policies[key] = copy.deepcopy(policy)
    
    policy_results = []
    
    # Define policy test ranges
    policy_options = {
        'purchase_rebate': [0, 10000, 20000, 40000],
        'stamp_duty_exemption': [0.0, 0.5, 1.0],
        'green_loan_subsidy': [0.0, 0.01, 0.02, 0.03],
        'carbon_price': [0, 30, 50, 100]
    }
    
    try:
        # Test each combination
        for rebate in policy_options['purchase_rebate']:
            for stamp_duty in policy_options['stamp_duty_exemption']:
                for loan_subsidy in policy_options['green_loan_subsidy']:
                    for carbon in policy_options['carbon_price']:
                        # Set policies
                        policies.POLICIES['purchase_rebate'].enabled = rebate > 0
                        policies.POLICIES['purchase_rebate'].amount = rebate
                        
                        policies.POLICIES['stamp_duty_exemption'].enabled = stamp_duty > 0
                        policies.POLICIES['stamp_duty_exemption'].exemption_percentage = stamp_duty
                        
                        policies.POLICIES['green_loan_subsidy'].enabled = loan_subsidy > 0
                        policies.POLICIES['green_loan_subsidy'].rate_reduction = loan_subsidy
                        
                        policies.POLICIES['carbon_price'].enabled = carbon > 0
                        policies.POLICIES['carbon_price'].price_per_tonne = carbon
                        
                        # Calculate impact across all vehicle pairs
                        tco_differences = []
                        vehicles_viable = 0
                        
                        for bev_inputs, diesel_inputs in vehicle_data.get_vehicle_pairs(scenario, purchase_method):
                            bev_tco = calculate_tco_from_inputs(bev_inputs)
                            diesel_tco = calculate_tco_from_inputs(diesel_inputs)
                            difference = bev_tco.total_cost - diesel_tco.total_cost
                            tco_differences.append(difference)
                            
                            if difference < 0:
                                vehicles_viable += 1
                        
                        avg_difference = np.mean(tco_differences)
                        
                        # Estimate policy cost
                        policy_cost = estimate_annual_policy_cost(
                            rebate, stamp_duty, loan_subsidy, carbon, scenario
                        )
                        
                        # Calculate cost effectiveness
                        baseline_diff = get_baseline_tco_difference(scenario, purchase_method)
                        tco_improvement = baseline_diff - avg_difference
                        cost_effectiveness = policy_cost / max(tco_improvement, 1)  # Avoid division by zero
                        
                        policy_results.append(PolicyImpactAnalysis(
                            policy_combination={
                                'purchase_rebate': rebate,
                                'stamp_duty_exemption': stamp_duty,
                                'green_loan_subsidy': loan_subsidy,
                                'carbon_price': carbon
                            },
                            avg_tco_difference=avg_difference,
                            vehicles_becoming_viable=vehicles_viable,
                            total_policy_cost=policy_cost,
                            cost_effectiveness=cost_effectiveness
                        ))
    
    finally:
        # Restore original policies
        for key, policy in original_policies.items():
            policies.POLICIES[key] = policy
    
    # Sort by cost effectiveness
    return sorted(policy_results, key=lambda x: x.cost_effectiveness)


def analyse_purchase_timing(
    vehicle_id: str,
    start_year: int = 2025,
    end_year: int = 2035,
    scenario: Optional[EconomicScenario] = None,
    purchase_method: str = 'financed'
) -> Dict[int, TCOResult]:
    """
    Analyse TCO impact of purchasing vehicle in different years.
    
    Adjusts scenario trajectories to account for purchase timing.
    """
    results = {}
    base_scenario = scenario or vehicle_data._default_scenario
    
    for purchase_year in range(start_year, end_year + 1):
        # Create adjusted scenario starting from purchase year
        years_offset = purchase_year - start_year
        
        if years_offset > 0:
            adjusted_scenario = copy.deepcopy(base_scenario)
            
            # Shift all trajectories
            for attr in ['diesel_price_trajectory', 'electricity_price_trajectory', 
                        'battery_price_trajectory', 'carbon_price_trajectory',
                        'bev_efficiency_improvement', 'diesel_efficiency_improvement',
                        'maintenance_cost_multiplier', 'bev_residual_value_multiplier']:
                trajectory = getattr(adjusted_scenario, attr)
                # Start trajectory from the offset year
                if len(trajectory) > years_offset:
                    setattr(adjusted_scenario, attr, trajectory[years_offset:])
                else:
                    # If we've gone past the trajectory, use last value
                    setattr(adjusted_scenario, attr, [trajectory[-1]] * const.VEHICLE_LIFE)
            
            # Adjust policy phase-out year if applicable
            if adjusted_scenario.policy_phase_out_year:
                adjusted_scenario.policy_phase_out_year -= years_offset
                
            vehicle_inputs = vehicle_data.get_vehicle(vehicle_id, adjusted_scenario, purchase_method)
        else:
            vehicle_inputs = vehicle_data.get_vehicle(vehicle_id, base_scenario, purchase_method)
        
        results[purchase_year] = calculate_tco_from_inputs(vehicle_inputs)
    
    return results


def estimate_annual_policy_cost(
    rebate: float,
    stamp_duty_exemption: float,
    loan_subsidy: float,
    carbon_price: float,
    scenario: Optional[EconomicScenario] = None
) -> float:
    """Estimate total annual cost of policy package to government."""
    # Estimate based on new vehicle sales
    estimated_bev_sales = 1000  # This should come from market data
    estimated_diesel_sales = 5000
    
    annual_cost = 0
    
    # Direct rebate cost
    annual_cost += rebate * estimated_bev_sales
    
    # Stamp duty revenue loss
    avg_bev_price = 300000  # Should calculate from vehicle data
    annual_cost += (avg_bev_price * const.STAMP_DUTY_RATE * stamp_duty_exemption) * estimated_bev_sales
    
    # Loan subsidy cost (simplified)
    if loan_subsidy > 0:
        avg_loan_amount = avg_bev_price * (1 - const.DOWN_PAYMENT_RATE)
        subsidy_cost_per_vehicle = avg_loan_amount * loan_subsidy * const.FINANCING_TERM
        annual_cost += subsidy_cost_per_vehicle * estimated_bev_sales / const.FINANCING_TERM
    
    # Carbon revenue (negative cost)
    if carbon_price > 0:
        avg_diesel_emissions = 30  # tonnes/year, should calculate
        annual_cost -= carbon_price * avg_diesel_emissions * estimated_diesel_sales
    
    return annual_cost


def get_baseline_tco_difference(
    scenario: Optional[EconomicScenario] = None,
    purchase_method: str = 'financed'
) -> float:
    """Get average TCO difference with no policies enabled."""
    # Temporarily disable all policies
    original_states = {}
    for key, policy in policies.POLICIES.items():
        original_states[key] = policy.enabled
        policy.enabled = False
    
    try:
        differences = []
        for bev_inputs, diesel_inputs in vehicle_data.get_vehicle_pairs(scenario, purchase_method):
            bev_tco = calculate_tco_from_inputs(bev_inputs)
            diesel_tco = calculate_tco_from_inputs(diesel_inputs)
            differences.append(bev_tco.total_cost - diesel_tco.total_cost)
        return np.mean(differences)
    finally:
        # Restore policy states
        for key, enabled in original_states.items():
            policies.POLICIES[key].enabled = enabled