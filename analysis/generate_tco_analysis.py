#!/usr/bin/env python3
"""
Generate comprehensive TCO analysis for light and medium rigid vehicles 
from 2024 to 2035 under the baseline scenario.

This script produces:
1. TCO calculations for all light and medium rigid vehicles
2. Year-by-year breakdown of costs
3. Complete readout of all variables, inputs, policies, and scenario parameters
"""

import sys
import os
from datetime import datetime
from typing import Dict, List
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import calculate_all_tcos, vehicle_data, VehicleInputs
from data.vehicles import ALL_MODELS, VehicleModel
from data.scenarios import SCENARIOS, set_active_scenario, get_active_scenario
from data.constants import *
from data.policies import POLICIES, get_active_policies
from calculations.inputs import vehicle_data


def filter_light_medium_rigid_vehicles() -> List[VehicleModel]:
    """Filter for light and medium rigid vehicles only."""
    return [
        vehicle for vehicle in ALL_MODELS 
        if vehicle.weight_class in ['Light Rigid', 'Medium Rigid']
    ]


def generate_year_by_year_costs(vehicle_inputs: VehicleInputs, start_year: int = 2024) -> Dict:
    """Generate detailed year-by-year cost breakdown for a vehicle."""
    yearly_breakdown = {}
    
    for year in range(1, VEHICLE_LIFE + 1):
        calendar_year = start_year + year - 1
        
        yearly_breakdown[calendar_year] = {
            'fuel_cost': vehicle_inputs.get_fuel_cost_year(year),
            'maintenance_cost': vehicle_inputs.get_maintenance_cost_year(year),
            'battery_replacement_cost': vehicle_inputs.get_battery_replacement_year(year),
            'carbon_cost': vehicle_inputs.get_carbon_cost_year(year),
            'depreciation': vehicle_inputs.get_depreciation_year(year),
            'insurance_cost': vehicle_inputs.annual_insurance_cost,
            'registration_cost': vehicle_inputs.vehicle.annual_registration,
        }
    
    return yearly_breakdown


def generate_scenario_summary(scenario_name: str = 'baseline') -> Dict:
    """Generate comprehensive summary of scenario parameters."""
    scenario = SCENARIOS[scenario_name]
    
    return {
        'scenario_name': scenario.name,
        'scenario_description': scenario.description,
        'price_trajectories': {
            'diesel_price_trajectory': scenario.diesel_price_trajectory,
            'electricity_price_trajectory': scenario.electricity_price_trajectory,
            'battery_price_trajectory': scenario.battery_price_trajectory,
            'carbon_price_trajectory': scenario.carbon_price_trajectory,
        },
        'technology_improvements': {
            'bev_efficiency_improvement': scenario.bev_efficiency_improvement,
            'diesel_efficiency_improvement': scenario.diesel_efficiency_improvement,
        },
        'cost_multipliers': {
            'maintenance_cost_multiplier': scenario.maintenance_cost_multiplier,
            'bev_residual_value_multiplier': getattr(scenario, 'bev_residual_value_multiplier', [1.0] * 15),
        },
        'policy_parameters': {
            'policy_phase_out_year': scenario.policy_phase_out_year,
            'road_user_charge_bev_start_year': scenario.road_user_charge_bev_start_year,
        }
    }


def generate_constants_summary() -> Dict:
    """Generate summary of all constants used in calculations."""
    return {
        'vehicle_parameters': {
            'vehicle_life': VEHICLE_LIFE,
            'rigid_annual_kms': RIGID_ANNUAL_KMS,
            'articulated_annual_kms': ART_ANNUAL_KMS,
        },
        'energy_costs': {
            'retail_charging_price': RETAIL_CHARGING_PRICE,
            'offpeak_charging_price': OFFPEAK_CHARGING_PRICE,
            'solar_charging_price': SOLAR_CHARGING_PRICE,
            'public_charging_price': PUBLIC_CHARGING_PRICE,
            'diesel_price': DIESEL_PRICE,
        },
        'charging_mix': {
            'rigid_retail_proportion': RIGID_RETAIL_PROPORTION,
            'rigid_offpeak_proportion': RIGID_OFFPEAK_PROPORTION,
            'rigid_solar_proportion': RIGID_SOLAR_PROPORTION,
            'rigid_public_proportion': RIGID_PUBLIC_PROPORTION,
            'articulated_retail_proportion': ART_RETAIL_PROPORTION,
            'articulated_offpeak_proportion': ART_OFFPEAK_PROPORTION,
            'articulated_solar_proportion': ART_SOLAR_PROPORTION,
            'articulated_public_proportion': ART_PUBLIC_PROPORTION,
        },
        'financial_parameters': {
            'discount_rate': DISCOUNT_RATE,
            'interest_rate': INTEREST_RATE,
            'inflation_rate': INFLATION_RATE,
            'financing_term': FINANCING_TERM,
            'down_payment_rate': DOWN_PAYMENT_RATE,
            'depreciation_rate_first_year': DEPRECIATION_RATE_FIRST_YEAR,
            'depreciation_rate_ongoing': DEPRECIATION_RATE_ONGOING,
        },
        'insurance_rates': {
            'insurance_rate_bev': INSURANCE_RATE_BEV,
            'insurance_rate_dsl': INSURANCE_RATE_DSL,
            'other_insurance': OTHER_INSURANCE,
        },
        'maintenance_costs': {
            'rigid_bev_maintenance_cost': RIGID_BEV_MAINTENANCE_COST,
            'articulated_bev_maintenance_cost': ART_BEV_MAINTENANCE_COST,
            'rigid_dsl_maintenance_cost': RIGID_DSL_MAINTENANCE_COST,
            'articulated_dsl_maintenance_cost': ART_DSL_MAINTENANCE_COST,
        },
        'battery_parameters': {
            'battery_replacement_cost': BATTERY_REPLACEMENT_COST,
            'battery_recycle_value': BATTERY_RECYCLE_VALUE,
            'battery_degradation_rate': BATTERY_DEGRADATION_RATE,
        },
        'taxes_and_fees': {
            'fuel_tax_credit': FUEL_TAX_CREDIT,
            'road_user_charge': ROAD_USER_CHARGE,
            'stamp_duty_rate': STAMP_DUTY_RATE,
        },
        'emissions_factors': {
            'retail_charging_emissions': RETAIL_CHARGING_EMISSIONS,
            'offpeak_charging_emissions': OFFPEAK_CHARGING_EMISSIONS,
            'solar_charging_emissions': SOLAR_CHARGING_EMISSIONS,
            'public_charging_emissions': PUBLIC_CHARGING_EMISSIONS,
            'diesel_emissions': DIESEL_EMISSIONS,
        }
    }


def generate_policies_summary() -> Dict:
    """Generate summary of current policy settings."""
    active_policies = get_active_policies()
    
    policy_summary = {
        'active_policies': {},
        'all_policies': {}
    }
    
    for key, policy in POLICIES.items():
        policy_info = {
            'name': policy.name,
            'description': policy.description,
            'enabled': policy.enabled,
        }
        
        # Add policy-specific parameters
        if hasattr(policy, 'amount'):
            policy_info['amount'] = policy.amount
        if hasattr(policy, 'percentage'):
            policy_info['percentage'] = policy.percentage
        if hasattr(policy, 'max_amount'):
            policy_info['max_amount'] = policy.max_amount
        if hasattr(policy, 'exemption_percentage'):
            policy_info['exemption_percentage'] = policy.exemption_percentage
        if hasattr(policy, 'price_per_tonne'):
            policy_info['price_per_tonne'] = policy.price_per_tonne
        if hasattr(policy, 'rate_reduction'):
            policy_info['rate_reduction'] = policy.rate_reduction
        if hasattr(policy, 'grant_percentage'):
            policy_info['grant_percentage'] = policy.grant_percentage
        
        policy_summary['all_policies'][key] = policy_info
        
        if policy.enabled:
            policy_summary['active_policies'][key] = policy_info
    
    return policy_summary


def main():
    """Generate comprehensive TCO analysis."""
    print("Generating TCO Analysis for Light and Medium Rigid Vehicles (2024-2035)")
    print("=" * 80)
    
    # Set baseline scenario
    set_active_scenario('baseline')
    scenario = get_active_scenario()
    
    # Filter vehicles
    target_vehicles = filter_light_medium_rigid_vehicles()
    print(f"\nAnalysing {len(target_vehicles)} vehicles:")
    for vehicle in target_vehicles:
        print(f"  - {vehicle.vehicle_id}: {vehicle.model_name} ({vehicle.drivetrain_type}, {vehicle.weight_class})")
    
    # Generate comprehensive analysis
    analysis_results = {
        'metadata': {
            'generation_timestamp': datetime.now().isoformat(),
            'analysis_period': '2024-2035',
            'scenario': 'baseline',
            'vehicle_types': 'Light Rigid and Medium Rigid',
            'total_vehicles_analysed': len(target_vehicles),
        },
        'scenario_parameters': generate_scenario_summary('baseline'),
        'constants': generate_constants_summary(),
        'policies': generate_policies_summary(),
        'vehicle_specifications': {},
        'tco_results': {},
        'yearly_cost_breakdowns': {}
    }
    
    # Calculate TCO for each vehicle
    print(f"\nCalculating TCOs under {scenario.name} scenario...")
    
    for vehicle in target_vehicles:
        print(f"Processing {vehicle.vehicle_id}...")
        
        # Store vehicle specifications
        analysis_results['vehicle_specifications'][vehicle.vehicle_id] = {
            'vehicle_id': vehicle.vehicle_id,
            'comparison_pair': vehicle.comparison_pair,
            'weight_class': vehicle.weight_class,
            'drivetrain_type': vehicle.drivetrain_type,
            'model_name': vehicle.model_name,
            'payload': vehicle.payload,
            'msrp': vehicle.msrp,
            'range_km': vehicle.range_km,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'kwh_per_km': vehicle.kwh_per_km,
            'litres_per_km': vehicle.litres_per_km,
            'battery_replacement_per_kw': vehicle.battery_replacement_per_kw,
            'maintenance_cost_per_km': vehicle.maintenance_cost_per_km,
            'annual_registration': vehicle.annual_registration,
            'annual_kms': vehicle.annual_kms,
            'noise_pollution_per_km': vehicle.noise_pollution_per_km,
        }
        
        # Get vehicle inputs for detailed analysis
        vehicle_inputs = vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, 'financed')
        
        # Calculate TCO
        from app import calculate_tco
        tco_result = calculate_tco(vehicle, scenario, 'financed')
        
        # Store TCO results
        analysis_results['tco_results'][vehicle.vehicle_id] = {
            'total_cost': tco_result.total_cost,
            'annual_cost': tco_result.annual_cost,
            'cost_per_km': tco_result.cost_per_km,
            'purchase_cost': tco_result.purchase_cost,
            'fuel_cost': tco_result.fuel_cost,
            'maintenance_cost': tco_result.maintenance_cost,
            'insurance_cost': tco_result.insurance_cost,
            'registration_cost': tco_result.registration_cost,
            'battery_replacement_cost': tco_result.battery_replacement_cost,
            'financing_cost': tco_result.financing_cost,
            'depreciation_cost': tco_result.depreciation_cost,
            'carbon_cost': tco_result.carbon_cost,
        }
        
        # Generate year-by-year breakdown
        analysis_results['yearly_cost_breakdowns'][vehicle.vehicle_id] = generate_year_by_year_costs(vehicle_inputs, 2024)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tco_analysis_baseline_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\nAnalysis complete! Results saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY OF TCO RESULTS")
    print("=" * 80)
    
    print(f"\nScenario: {scenario.name} - {scenario.description}")
    print(f"Analysis Period: 2024-2035")
    print(f"Vehicle Life: {VEHICLE_LIFE} years")
    print(f"Discount Rate: {DISCOUNT_RATE:.1%}")
    
    print(f"\nTCO Results (NPV, AUD):")
    print("-" * 60)
    print(f"{'Vehicle ID':<12} {'Model':<25} {'Type':<8} {'Total TCO':<12} {'Annual':<10} {'$/km':<8}")
    print("-" * 60)
    
    for vehicle_id, tco in analysis_results['tco_results'].items():
        vehicle = next(v for v in target_vehicles if v.vehicle_id == vehicle_id)
        print(f"{vehicle_id:<12} {vehicle.model_name[:24]:<25} {vehicle.drivetrain_type:<8} "
              f"${tco['total_cost']:>10,.0f} ${tco['annual_cost']:>8,.0f} ${tco['cost_per_km']:>6.2f}")
    
    print(f"\nDetailed analysis with year-by-year breakdowns saved to: {output_file}")
    
    return analysis_results


if __name__ == "__main__":
    main() 