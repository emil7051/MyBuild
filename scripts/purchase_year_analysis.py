#!/usr/bin/env python3
"""
Analyse how TCO changes for vehicles purchased in different years (2024-2030)
under the baseline scenario, accounting for evolving technology and prices.

This analysis shows:
1. How purchase prices change over time (especially for BEVs with falling battery costs)
2. How operating costs evolve based on purchase year
3. The changing economics between BEV and diesel over time
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import calculate_tco, vehicle_data
from data.vehicles import ALL_MODELS, VehicleModel, BY_ID
from data.scenarios import SCENARIOS, EconomicScenario
from data.constants import VEHICLE_LIFE
from calculations.inputs import VehicleInputs


def create_purchase_year_scenario(base_scenario: EconomicScenario, purchase_year: int) -> EconomicScenario:
    """
    Create a scenario adjusted for a specific purchase year.
    
    Args:
        base_scenario: The baseline scenario
        purchase_year: Calendar year of purchase (e.g., 2025)
    
    Returns:
        Adjusted scenario starting from the purchase year
    """
    # Calculate years since baseline start (2024)
    years_offset = purchase_year - 2024
    
    # Extend trajectories if needed to cover full vehicle life from purchase year
    def extend_trajectory(trajectory: List[float], default_growth: float = 0.0) -> List[float]:
        """Extend trajectory to cover full vehicle life from purchase year."""
        if not trajectory:
            return [1.0] * VEHICLE_LIFE
        
        extended = trajectory.copy()
        
        # If we need more years, extend based on the trend
        while len(extended) < years_offset + VEHICLE_LIFE:
            if len(extended) >= 2 and extended[-2] != 0:
                # Calculate growth rate from last two values
                growth_rate = (extended[-1] / extended[-2]) - 1
            else:
                growth_rate = default_growth
            
            if extended[-1] == 0 and growth_rate == 0:
                # If last value is zero and no growth, keep extending with zeros
                next_value = 0
            else:
                next_value = extended[-1] * (1 + growth_rate)
            extended.append(next_value)
        
        # Extract the relevant 15-year period starting from purchase year
        start_idx = years_offset
        end_idx = start_idx + VEHICLE_LIFE
        
        return extended[start_idx:end_idx]
    
    # Create adjusted trajectories
    adjusted_scenario = EconomicScenario(
        name=f"{base_scenario.name} ({purchase_year})",
        description=f"{base_scenario.description} - Purchase year {purchase_year}",
        diesel_price_trajectory=extend_trajectory(base_scenario.diesel_price_trajectory, 0.03),
        electricity_price_trajectory=extend_trajectory(base_scenario.electricity_price_trajectory, 0.02),
        battery_price_trajectory=extend_trajectory(base_scenario.battery_price_trajectory, -0.07),
        carbon_price_trajectory=extend_trajectory(base_scenario.carbon_price_trajectory, 0.0),
        bev_efficiency_improvement=extend_trajectory(base_scenario.bev_efficiency_improvement, -0.02),
        diesel_efficiency_improvement=extend_trajectory(base_scenario.diesel_efficiency_improvement, -0.01),
        maintenance_cost_multiplier=extend_trajectory(base_scenario.maintenance_cost_multiplier, 0.0),
        bev_residual_value_multiplier=extend_trajectory(
            getattr(base_scenario, 'bev_residual_value_multiplier', [1.0] * 15), 0.0
        ),
        policy_phase_out_year=base_scenario.policy_phase_out_year,
        road_user_charge_bev_start_year=base_scenario.road_user_charge_bev_start_year
    )
    
    return adjusted_scenario


def calculate_adjusted_vehicle_price(vehicle: VehicleModel, purchase_year: int, base_scenario: EconomicScenario) -> float:
    """
    Calculate the adjusted vehicle price for a given purchase year.
    For BEVs, this accounts for falling battery costs.
    For diesel vehicles, prices remain constant.
    """
    years_offset = purchase_year - 2024
    
    if vehicle.drivetrain_type == 'BEV' and years_offset > 0:
        # Apply battery cost reductions to the vehicle price
        # Assuming battery is ~40% of BEV price and using battery trajectory
        if years_offset < len(base_scenario.battery_price_trajectory):
            battery_cost_multiplier = base_scenario.battery_price_trajectory[years_offset]
        else:
            # Extrapolate battery cost decline
            battery_cost_multiplier = base_scenario.battery_price_trajectory[-1] * (0.93 ** (years_offset - len(base_scenario.battery_price_trajectory) + 1))
        
        # Apply reduction only to battery portion of vehicle price
        battery_portion = 0.4  # Assume 40% of BEV price is battery
        non_battery_portion = 1 - battery_portion
        
        adjusted_price = vehicle.msrp * (non_battery_portion + battery_portion * battery_cost_multiplier)
        return adjusted_price
    
    return vehicle.msrp


def analyse_purchase_years(start_year: int = 2024, end_year: int = 2030) -> Dict:
    """
    Analyse TCO for different purchase years.
    
    Args:
        start_year: First purchase year to analyse
        end_year: Last purchase year to analyse
    
    Returns:
        Dictionary with analysis results
    """
    base_scenario = SCENARIOS['baseline']
    
    # Filter to light and medium rigid vehicles
    target_vehicles = [
        vehicle for vehicle in ALL_MODELS 
        if vehicle.weight_class in ['Light Rigid', 'Medium Rigid']
    ]
    
    results = {
        'metadata': {
            'analysis_type': 'Purchase Year Analysis',
            'base_scenario': base_scenario.name,
            'purchase_years': list(range(start_year, end_year + 1)),
            'vehicle_life': VEHICLE_LIFE,
            'generation_timestamp': datetime.now().isoformat(),
        },
        'vehicle_specifications': {},
        'purchase_year_analysis': {},
        'summary_by_year': {},
        'bev_vs_diesel_savings': {}
    }
    
    # Store vehicle specifications
    for vehicle in target_vehicles:
        results['vehicle_specifications'][vehicle.vehicle_id] = {
            'vehicle_id': vehicle.vehicle_id,
            'model_name': vehicle.model_name,
            'weight_class': vehicle.weight_class,
            'drivetrain_type': vehicle.drivetrain_type,
            'base_msrp': vehicle.msrp,
            'comparison_pair': vehicle.comparison_pair
        }
    
    # Analyse each purchase year
    for purchase_year in range(start_year, end_year + 1):
        print(f"Analysing purchase year {purchase_year}...")
        
        # Create scenario for this purchase year
        year_scenario = create_purchase_year_scenario(base_scenario, purchase_year)
        
        year_results = {}
        
        for vehicle in target_vehicles:
            # Calculate adjusted vehicle price
            adjusted_price = calculate_adjusted_vehicle_price(vehicle, purchase_year, base_scenario)
            
            # Create adjusted vehicle model
            adjusted_vehicle = VehicleModel(
                vehicle_id=vehicle.vehicle_id,
                comparison_pair=vehicle.comparison_pair,
                weight_class=vehicle.weight_class,
                drivetrain_type=vehicle.drivetrain_type,
                model_name=vehicle.model_name,
                payload=vehicle.payload,
                msrp=adjusted_price,
                range_km=vehicle.range_km,
                battery_capacity_kwh=vehicle.battery_capacity_kwh,
                kwh_per_km=vehicle.kwh_per_km,
                litres_per_km=vehicle.litres_per_km,
                battery_replacement_per_kw=vehicle.battery_replacement_per_kw,
                maintenance_cost_per_km=vehicle.maintenance_cost_per_km,
                annual_registration=vehicle.annual_registration,
                annual_kms=vehicle.annual_kms,
                noise_pollution_per_km=vehicle.noise_pollution_per_km
            )
            
            # Calculate TCO
            tco_result = calculate_tco(adjusted_vehicle, year_scenario, 'financed')
            
            year_results[vehicle.vehicle_id] = {
                'adjusted_msrp': adjusted_price,
                'price_change_from_2024': adjusted_price - vehicle.msrp,
                'price_change_percent': ((adjusted_price - vehicle.msrp) / vehicle.msrp) * 100,
                'total_tco': tco_result.total_cost,
                'annual_cost': tco_result.annual_cost,
                'cost_per_km': tco_result.cost_per_km,
                'fuel_cost': tco_result.fuel_cost,
                'maintenance_cost': tco_result.maintenance_cost,
                'battery_replacement_cost': tco_result.battery_replacement_cost,
                'financing_cost': tco_result.financing_cost,
                'purchase_cost': tco_result.purchase_cost
            }
        
        results['purchase_year_analysis'][purchase_year] = year_results
        
        # Calculate summary statistics for this year
        bev_tcos = [data['total_tco'] for vid, data in year_results.items() 
                   if BY_ID[vid].drivetrain_type == 'BEV']
        diesel_tcos = [data['total_tco'] for vid, data in year_results.items() 
                      if BY_ID[vid].drivetrain_type == 'Diesel']
        
        results['summary_by_year'][purchase_year] = {
            'avg_bev_tco': sum(bev_tcos) / len(bev_tcos) if bev_tcos else 0,
            'avg_diesel_tco': sum(diesel_tcos) / len(diesel_tcos) if diesel_tcos else 0,
            'avg_bev_cost_per_km': sum([data['cost_per_km'] for vid, data in year_results.items() 
                                      if BY_ID[vid].drivetrain_type == 'BEV']) / len(bev_tcos) if bev_tcos else 0,
            'avg_diesel_cost_per_km': sum([data['cost_per_km'] for vid, data in year_results.items() 
                                         if BY_ID[vid].drivetrain_type == 'Diesel']) / len(diesel_tcos) if diesel_tcos else 0,
        }
        
        # Calculate BEV vs diesel savings for comparison pairs
        year_savings = {}
        for vehicle in target_vehicles:
            if vehicle.drivetrain_type == 'BEV':
                bev_tco = year_results[vehicle.vehicle_id]['total_tco']
                diesel_id = vehicle.comparison_pair
                if diesel_id in year_results:
                    diesel_tco = year_results[diesel_id]['total_tco']
                    savings = diesel_tco - bev_tco
                    savings_percent = (savings / diesel_tco) * 100
                    
                    year_savings[f"{vehicle.vehicle_id}_vs_{diesel_id}"] = {
                        'bev_model': vehicle.model_name,
                        'diesel_model': BY_ID[diesel_id].model_name,
                        'weight_class': vehicle.weight_class,
                        'absolute_savings': savings,
                        'percent_savings': savings_percent,
                        'bev_tco': bev_tco,
                        'diesel_tco': diesel_tco
                    }
        
        results['bev_vs_diesel_savings'][purchase_year] = year_savings
    
    return results


def create_summary_tables(results: Dict) -> str:
    """Create formatted summary tables from the analysis results."""
    
    summary = []
    summary.append("# Purchase Year Analysis: TCO Changes Over Time")
    summary.append("## Baseline Scenario with Technology Evolution\n")
    
    # TCO by Purchase Year Summary
    summary.append("## Average TCO by Purchase Year\n")
    summary.append("| Purchase Year | Avg BEV TCO | Avg Diesel TCO | BEV Cost/km | Diesel Cost/km | BEV Advantage |")
    summary.append("|---------------|-------------|----------------|-------------|----------------|---------------|")
    
    for year, data in results['summary_by_year'].items():
        bev_tco = data['avg_bev_tco']
        diesel_tco = data['avg_diesel_tco']
        advantage = ((diesel_tco - bev_tco) / diesel_tco * 100) if diesel_tco > 0 else 0
        
        summary.append(f"| {year} | ${bev_tco:,.0f} | ${diesel_tco:,.0f} | ${data['avg_bev_cost_per_km']:.2f} | ${data['avg_diesel_cost_per_km']:.2f} | {advantage:.1f}% |")
    
    # BEV Price Evolution
    summary.append("\n## BEV Price Evolution (Technology Cost Reductions)\n")
    summary.append("| Vehicle | 2024 Price | 2025 Price | 2026 Price | 2027 Price | 2028 Price | 2029 Price | 2030 Price |")
    summary.append("|---------|------------|------------|------------|------------|------------|------------|------------|")
    
    for vehicle_id, spec in results['vehicle_specifications'].items():
        if spec['drivetrain_type'] == 'BEV':
            row = [f"| {spec['model_name'][:20]}"]
            for year in range(2024, 2031):
                if year in results['purchase_year_analysis']:
                    price = results['purchase_year_analysis'][year][vehicle_id]['adjusted_msrp']
                    row.append(f"${price:,.0f}")
                else:
                    row.append("-")
            summary.append(" | ".join(row) + " |")
    
    # Comparison Pair Savings Evolution
    summary.append("\n## BEV vs Diesel Savings by Purchase Year\n")
    
    # Get first comparison pair as example
    first_year = min(results['bev_vs_diesel_savings'].keys())
    first_comparison = list(results['bev_vs_diesel_savings'][first_year].keys())[0]
    
    summary.append("| Purchase Year | Comparison | BEV Savings | Savings % |")
    summary.append("|---------------|------------|-------------|-----------|")
    
    for year in sorted(results['bev_vs_diesel_savings'].keys()):
        for comparison_id, data in results['bev_vs_diesel_savings'][year].items():
            summary.append(f"| {year} | {data['bev_model'][:15]} vs {data['diesel_model'][:15]} | "
                         f"${data['absolute_savings']:,.0f} | {data['percent_savings']:.1f}% |")
    
    return "\n".join(summary)


def main():
    """Run the purchase year analysis."""
    print("Purchase Year Analysis: TCO Evolution (2024-2030)")
    print("=" * 60)
    
    # Run analysis
    results = analyse_purchase_years(2024, 2030)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"purchase_year_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Create and save summary
    summary_text = create_summary_tables(results)
    summary_file = f"purchase_year_summary_{timestamp}.md"
    
    with open(summary_file, 'w') as f:
        f.write(summary_text)
    
    print(f"\nAnalysis complete!")
    print(f"Detailed results: {output_file}")
    print(f"Summary report: {summary_file}")
    
    # Print key findings
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    
    print("\nAverage TCO Evolution:")
    print("-" * 40)
    for year in [2024, 2026, 2028, 2030]:
        if year in results['summary_by_year']:
            data = results['summary_by_year'][year]
            bev_avg = data['avg_bev_tco']
            diesel_avg = data['avg_diesel_tco']
            advantage = ((diesel_avg - bev_avg) / diesel_avg * 100) if diesel_avg > 0 else 0
            
            print(f"{year}: BEV ${bev_avg:,.0f} vs Diesel ${diesel_avg:,.0f} "
                  f"(BEV {advantage:.1f}% cheaper)")
    
    # Show price evolution for one BEV
    bev_vehicle = next(v for v in results['vehicle_specifications'].values() 
                      if v['drivetrain_type'] == 'BEV')
    print(f"\n{bev_vehicle['model_name']} Price Evolution:")
    print("-" * 40)
    for year in [2024, 2026, 2028, 2030]:
        if year in results['purchase_year_analysis']:
            price = results['purchase_year_analysis'][year][bev_vehicle['vehicle_id']]['adjusted_msrp']
            base_price = bev_vehicle['base_msrp']
            change = ((price - base_price) / base_price) * 100
            print(f"{year}: ${price:,.0f} ({change:+.1f}% vs 2024)")
    
    return results


if __name__ == "__main__":
    main() 