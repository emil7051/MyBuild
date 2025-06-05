import numpy as np
import numpy_financial as npf
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass

from data.vehicles import VehicleModel, BY_ID
import data.constants as const
from data.scenarios import EconomicScenario, get_active_scenario
from calculations.inputs import vehicle_data, VehicleInputs
from calculations.utils import calculate_present_value, discount_to_present


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
    depreciation_cost: float
    carbon_cost: float = 0.0
    charging_labour_cost: float = 0.0
    scenario_name: str = "baseline"


def calculate_tco_from_inputs(vehicle_inputs: VehicleInputs) -> TCOResult:
    """Calculate total cost of ownership using pre-calculated vehicle inputs."""
    
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
        npv_monthly_payments = 0.0
        monthly_payment = vehicle_inputs.monthly_payment
        num_payments = const.FINANCING_TERM * 12
        
        for month in range(1, num_payments + 1):
            # Calculate the discount factor for this month
            year_fraction = month / 12.0
            discount_factor = (1 + const.DISCOUNT_RATE) ** year_fraction
            npv_monthly_payments += monthly_payment / discount_factor
        
        npv_purchase_payments = npv_down_payment + npv_monthly_payments
    
    # Calculate depreciation over vehicle life with discounting
    total_depreciation = 0.0
    for year in range(1, const.VEHICLE_LIFE + 1):
        annual_depreciation = vehicle_inputs.get_depreciation_year(year)
        total_depreciation += discount_to_present(annual_depreciation, year)
    
    # Annual costs over vehicle life with discounting
    total_fuel_cost = 0.0
    total_battery_cost = 0.0
    total_carbon_cost = 0.0
    total_maintenance_cost = 0.0
    total_charging_labour_cost = 0.0
    
    for year in range(1, const.VEHICLE_LIFE + 1):
        # Get year-specific costs
        annual_fuel = vehicle_inputs.get_fuel_cost_year(year)
        battery_cost = vehicle_inputs.get_battery_replacement_year(year)
        carbon_cost = vehicle_inputs.get_carbon_cost_year(year)
        maintenance_cost = vehicle_inputs.get_maintenance_cost_year(year)
        charging_labour_cost = vehicle_inputs.get_charging_labour_cost_year(year)
        
        # Discount to present value
        total_fuel_cost += discount_to_present(annual_fuel, year)
        total_battery_cost += discount_to_present(battery_cost, year)
        total_carbon_cost += discount_to_present(carbon_cost, year)
        total_maintenance_cost += discount_to_present(maintenance_cost, year)
        total_charging_labour_cost += discount_to_present(charging_labour_cost, year)
    
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
        total_charging_labour_cost -
        total_depreciation
    )
    
    # Calculate annual equivalent and cost per km
    annual_cost = total_cost / const.VEHICLE_LIFE
    cost_per_km = annual_cost / vehicle_inputs.vehicle.annual_kms
    
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
        depreciation_cost=total_depreciation,  # NPV of depreciation
        carbon_cost=total_carbon_cost,
        charging_labour_cost=total_charging_labour_cost,
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


# Legacy compatibility functions (using original function signatures)
def calculate_purchase_cost(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate total purchase cost including stamp duty."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).initial_cost


def calculate_annual_fuel_cost(vehicle: VehicleModel, year: int = 1, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate annual fuel cost for a vehicle in a given year."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).get_fuel_cost_year(year)


def calculate_annual_maintenance_cost(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate annual maintenance cost based on vehicle type and drivetrain."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).annual_maintenance_cost


def calculate_annual_insurance_cost(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate annual insurance cost."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).annual_insurance_cost


def calculate_battery_replacement_cost(vehicle: VehicleModel, year: int, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate battery replacement cost for BEV in a given year."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).get_battery_replacement_year(year)


def calculate_financing_cost(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate total financing cost over the financing term."""
    return vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method).total_financing_cost


def calculate_depreciation_cost(vehicle: VehicleModel, scenario: Optional[EconomicScenario] = None, purchase_method: Literal['outright', 'financed'] = 'financed') -> float:
    """Calculate total depreciation cost over vehicle life."""
    vehicle_inputs = vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, purchase_method)
    total_depreciation = 0.0
    for year in range(1, const.VEHICLE_LIFE + 1):
        total_depreciation += vehicle_inputs.get_depreciation_year(year)
    return total_depreciation
