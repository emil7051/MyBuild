import numpy as np
import numpy_financial as npf
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass

from data.vehicles import VehicleModel, BY_ID
import data.constants as const
from data.scenarios import EconomicScenario, get_active_scenario
from .inputs import vehicle_data, VehicleInputs
from .utils import calculate_present_value, discount_to_present, calculate_annualised_cost, calculate_npv_of_payments, calculate_npv_of_annual_cashflows


@dataclass
class TCOResult:
    """Results of TCO calculation for a vehicle."""
    vehicle_id: str
    total_cost: float
    annual_cost: float
    cost_per_km: float
    purchase_cost: float
    fuel_cost: float
    maintenance_cost: float
    insurance_cost: float
    registration_cost: float
    battery_replacement_cost: float
    financing_cost: float
    residual_value: float = 0.0  # Present value of residual value at end of vehicle life
    carbon_cost: float = 0.0
    charging_labour_cost: float = 0.0
    payload_penalty_cost: float = 0.0
    scenario_name: str = "baseline"


def calculate_tco_from_inputs(vehicle_inputs: VehicleInputs, overrides: Optional[Dict[str, float]] = None) -> TCOResult:
    """Calculate total cost of ownership using pre-calculated vehicle inputs and optional overrides."""
    
    # Get annual kms with potential override
    annual_kms = vehicle_inputs.get_annual_kms(overrides)
    
    # Initial costs depend on purchase method
    if vehicle_inputs.purchase_method == 'outright':
        # Outright purchase: pay full initial cost upfront, no financing
        upfront_cost = vehicle_inputs.initial_cost
        financing_cost = 0.0
        npv_purchase_payments = vehicle_inputs.initial_cost  # Full amount paid in year 0
    else:
        # Financed: pay only down payment upfront
        upfront_cost = vehicle_inputs.down_payment
        financing_cost = vehicle_inputs.total_financing_cost
        
        # Calculate NPV of all purchase-related payments
        npv_down_payment = vehicle_inputs.down_payment  # Paid in year 0
        
        # Calculate NPV of monthly loan payments
        num_payments = const.FINANCING_TERM * 12
        npv_monthly_payments = calculate_npv_of_payments(
            vehicle_inputs.monthly_payment,
            num_payments,
            const.DISCOUNT_RATE
        )
        
        npv_purchase_payments = npv_down_payment + npv_monthly_payments
    
    # Calculate residual value at end of vehicle life and discount to present
    residual_value_future = vehicle_inputs.get_residual_value(const.VEHICLE_LIFE, overrides)
    residual_value_pv = discount_to_present(residual_value_future, const.VEHICLE_LIFE)
    
    # Generate lists of annual costs over vehicle life
    annual_fuel_costs = [vehicle_inputs.get_fuel_cost_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    annual_battery_costs = [vehicle_inputs.get_battery_replacement_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    annual_carbon_costs = [vehicle_inputs.get_carbon_cost_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    annual_maintenance_costs = [vehicle_inputs.get_maintenance_cost_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    annual_charging_labour_costs = [vehicle_inputs.get_charging_labour_cost_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    annual_payload_penalties = [vehicle_inputs.get_payload_penalty_year(year, overrides) for year in range(1, const.VEHICLE_LIFE + 1)]
    
    # Calculate NPV of all operating costs
    total_fuel_cost = calculate_npv_of_annual_cashflows(annual_fuel_costs)
    total_battery_cost = calculate_npv_of_annual_cashflows(annual_battery_costs)
    total_carbon_cost = calculate_npv_of_annual_cashflows(annual_carbon_costs)
    total_maintenance_cost = calculate_npv_of_annual_cashflows(annual_maintenance_costs)
    total_charging_labour_cost = calculate_npv_of_annual_cashflows(annual_charging_labour_costs)
    total_payload_penalty = calculate_npv_of_annual_cashflows(annual_payload_penalties)
    
    # Fixed annual costs (present value)
    total_insurance_pv = calculate_present_value(vehicle_inputs.annual_insurance_cost, const.VEHICLE_LIFE)
    total_registration_pv = calculate_present_value(vehicle_inputs.vehicle.annual_registration, const.VEHICLE_LIFE)
    
    # Total TCO using NPV of purchase payments
    total_cost = (
        npv_purchase_payments +  # NPV of all purchase-related payments
        total_fuel_cost + 
        total_maintenance_cost + 
        total_insurance_pv + 
        total_registration_pv + 
        total_battery_cost + 
        total_carbon_cost +
        total_charging_labour_cost +
        total_payload_penalty -
        residual_value_pv
    )
    
    # Calculate annual equivalent and cost per km using potentially overridden annual_kms
    annual_cost = calculate_annualised_cost(total_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE)
    cost_per_km = annual_cost / annual_kms
    
    return TCOResult(
        vehicle_id=vehicle_inputs.vehicle.vehicle_id,
        total_cost=total_cost,
        annual_cost=annual_cost,
        cost_per_km=cost_per_km,
        purchase_cost=upfront_cost,  # Actual upfront payment
        fuel_cost=total_fuel_cost,
        maintenance_cost=total_maintenance_cost,
        insurance_cost=vehicle_inputs.annual_insurance_cost * const.VEHICLE_LIFE,      # Undiscounted for reporting
        registration_cost=vehicle_inputs.vehicle.annual_registration * const.VEHICLE_LIFE,  # Undiscounted for reporting
        battery_replacement_cost=total_battery_cost,
        financing_cost=financing_cost,
        residual_value=residual_value_pv,  # Present value of residual value
        carbon_cost=total_carbon_cost,
        charging_labour_cost=total_charging_labour_cost,
        payload_penalty_cost=total_payload_penalty,
        scenario_name=vehicle_inputs.scenario.name
    )


def calculate_tco(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> TCOResult:
    """Calculate TCO for a vehicle model with optional scenario and purchase method."""
    vehicle_inputs = vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method)
    return calculate_tco_from_inputs(vehicle_inputs)


def calculate_all_tcos(scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> Dict[str, TCOResult]:
    """Calculate TCO for all vehicles in the database."""
    results = {}
    for vehicle_id, vehicle_inputs in vehicle_data.get_all_vehicles(scenario, purchase_method).items():
        results[vehicle_id] = calculate_tco_from_inputs(vehicle_inputs)
    return results


def compare_vehicle_pairs(scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> List[Tuple[TCOResult, TCOResult, float]]:
    """Compare TCO between BEV and diesel pairs, returning cost difference."""
    comparisons = []
    
    for bev_inputs, diesel_inputs in vehicle_data.get_vehicle_pairs(scenario, purchase_method):
        bev_tco = calculate_tco_from_inputs(bev_inputs)
        diesel_tco = calculate_tco_from_inputs(diesel_inputs)
        cost_difference = bev_tco.total_cost - diesel_tco.total_cost
        comparisons.append((bev_tco, diesel_tco, cost_difference))
    
    return comparisons


def calculate_scenario_comparison(vehicle_id: str, scenarios: List[EconomicScenario], purchase_method: Literal['outright', 'financed'] = 'financed') -> Dict[str, TCOResult]:
    """Calculate TCO for a single vehicle across multiple scenarios."""
    results = {}
    for scenario in scenarios:
        vehicle_inputs = vehicle_data.get_vehicle(vehicle_id, scenario, purchase_method)
        results[scenario.name] = calculate_tco_from_inputs(vehicle_inputs)
    return results


def calculate_breakeven_analysis(bev_id: str, diesel_id: str, scenarios: List[EconomicScenario], purchase_method: Literal['outright', 'financed'] = 'financed') -> Dict[str, float]:
    """Calculate TCO difference between BEV and diesel across multiple scenarios."""
    breakeven_results = {}
    
    for scenario in scenarios:
        bev_inputs = vehicle_data.get_vehicle(bev_id, scenario, purchase_method)
        diesel_inputs = vehicle_data.get_vehicle(diesel_id, scenario, purchase_method)
        
        bev_tco = calculate_tco_from_inputs(bev_inputs)
        diesel_tco = calculate_tco_from_inputs(diesel_inputs)
        
        # Positive means BEV is more expensive, negative means BEV is cheaper
        breakeven_results[scenario.name] = bev_tco.total_cost - diesel_tco.total_cost
    
    return breakeven_results
