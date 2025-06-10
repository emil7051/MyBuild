"""
Report generation functions for TCO analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from calculations.calculations import TCOResult, compare_vehicle_pairs, calculate_tco_from_inputs
from calculations.inputs import vehicle_data
from .analysis import calculate_payback_analysis, analyse_purchase_timing
from data import constants as const
from data.vehicles import BY_ID


def generate_executive_summary(
    comparisons: List[Tuple[TCOResult, TCOResult, float]],
    scenario_name: str = "Current"
) -> Dict:
    """
    Generate executive summary metrics from vehicle comparisons.
    
    Args:
        comparisons: List of (BEV TCO, Diesel TCO, difference) tuples
        scenario_name: Name of the scenario for context
        
    Returns:
        Dictionary containing key metrics and insights
    """
    summary = {
        'scenario': scenario_name,
        'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'overview': {},
        'by_class': {},
        'key_findings': [],
        'recommendations': []
    }
    
    # Overall metrics
    total_vehicles = len(comparisons)
    bev_cheaper = [(b, d, diff) for b, d, diff in comparisons if diff < 0]
    
    summary['overview'] = {
        'total_vehicle_pairs': total_vehicles,
        'bev_cost_competitive': len(bev_cheaper),
        'percentage_competitive': (len(bev_cheaper) / total_vehicles * 100) if total_vehicles > 0 else 0,
        'average_additional_cost': np.mean([diff for _, _, diff in comparisons if diff > 0]) if any(diff > 0 for _, _, diff in comparisons) else 0,
        'average_savings': -np.mean([diff for _, _, diff in comparisons if diff < 0]) if bev_cheaper else 0,
        'best_case_savings': -min(diff for _, _, diff in comparisons) if comparisons else 0,
        'worst_case_cost': max(diff for _, _, diff in comparisons) if comparisons else 0
    }
    
    # Analysis by vehicle class
    by_class = defaultdict(list)
    for bev, diesel, diff in comparisons:
        vehicle = BY_ID[bev.vehicle_id]
        by_class[vehicle.weight_class].append((bev, diesel, diff))
    
    for weight_class, class_comparisons in by_class.items():
        diffs = [diff for _, _, diff in class_comparisons]
        competitive = sum(1 for _, _, diff in class_comparisons if diff < 0)
        
        summary['by_class'][weight_class] = {
            'total_models': len(class_comparisons),
            'competitive_models': competitive,
            'avg_tco_difference': np.mean(diffs),
            'min_difference': min(diffs),
            'max_difference': max(diffs),
            'best_performing_pair': None,
            'payback_years': {}
        }
        
        # Find best performing pair and calculate payback
        best_pair = min(class_comparisons, key=lambda x: x[2])
        if best_pair[2] < 0:  # Only if BEV is cheaper
            bev_inputs = vehicle_data.get_vehicle(best_pair[0].vehicle_id)
            diesel_inputs = vehicle_data.get_vehicle(best_pair[1].vehicle_id)
            payback = calculate_payback_analysis(bev_inputs, diesel_inputs)
            
            summary['by_class'][weight_class]['best_performing_pair'] = {
                'bev_model': BY_ID[best_pair[0].vehicle_id].model_name,
                'diesel_model': BY_ID[best_pair[1].vehicle_id].model_name,
                'tco_savings': -best_pair[2],
                'payback_years': payback.payback_years if payback.breakeven_achieved else None
            }
    
    # Generate key findings
    if summary['overview']['percentage_competitive'] > 50:
        summary['key_findings'].append(
            f"Majority ({summary['overview']['percentage_competitive']:.0f}%) of BEV models are cost-competitive"
        )
    
    # Best performing class
    best_class = min(summary['by_class'].items(), 
                    key=lambda x: x[1]['avg_tco_difference'])
    if best_class[1]['avg_tco_difference'] < 0:
        summary['key_findings'].append(
            f"{best_class[0]} trucks show strongest BEV economics with average savings of ${-best_class[1]['avg_tco_difference']:,.0f}"
        )
    
    # Generate recommendations
    if summary['overview']['percentage_competitive'] < 30:
        summary['recommendations'].append(
            "Consider policy interventions to improve BEV competitiveness"
        )
    
    for weight_class, metrics in summary['by_class'].items():
        if metrics['competitive_models'] == 0:
            summary['recommendations'].append(
                f"Target incentives for {weight_class} segment where no BEVs are currently competitive"
            )
    
    return summary


def generate_fleet_report(
    fleet_composition: Dict[str, int],
    scenario_name: str = "Current"
) -> pd.DataFrame:
    """
    Generate detailed fleet transition report.
    
    Args:
        fleet_composition: Dict of vehicle_id -> quantity
        scenario_name: Scenario to use for analysis
        
    Returns:
        DataFrame with detailed fleet analysis
    """
    report_data = []
    
    for vehicle_id, quantity in fleet_composition.items():
        if vehicle_id not in BY_ID:
            continue
            
        vehicle = BY_ID[vehicle_id]
        
        # Skip if diesel vehicle
        if vehicle.drivetrain_type != 'BEV':
            continue
            
        # Get TCO for BEV and comparison diesel
        bev_inputs = vehicle_data.get_vehicle(vehicle_id)
        bev_tco = calculate_tco_from_inputs(bev_inputs)
        
        if vehicle.comparison_pair and vehicle.comparison_pair in BY_ID:
            diesel_inputs = vehicle_data.get_vehicle(vehicle.comparison_pair)
            diesel_tco = calculate_tco_from_inputs(diesel_inputs)
            
            # Calculate payback
            payback = calculate_payback_analysis(bev_inputs, diesel_inputs)
            
            # Annual emissions reduction
            diesel_emissions = (diesel_inputs.vehicle.litres_per_km * 
                              diesel_inputs.vehicle.annual_kms * 
                              const.DIESEL_EMISSIONS / 1000)  # tonnes
            
            report_data.append({
                'vehicle_model': vehicle.model_name,
                'weight_class': vehicle.weight_class,
                'quantity': quantity,
                'unit_capex_premium': bev_inputs.initial_cost - diesel_inputs.initial_cost,
                'fleet_capex_premium': (bev_inputs.initial_cost - diesel_inputs.initial_cost) * quantity,
                'unit_annual_savings': diesel_tco.annual_cost - bev_tco.annual_cost,
                'fleet_annual_savings': (diesel_tco.annual_cost - bev_tco.annual_cost) * quantity,
                'payback_years': payback.payback_years if payback.breakeven_achieved else None,
                'unit_emissions_reduction': diesel_emissions,
                'fleet_emissions_reduction': diesel_emissions * quantity,
                '15yr_tco_savings': payback.total_savings_15yr * quantity,
                '15yr_npv_savings': payback.npv_savings * quantity
            })
    
    df = pd.DataFrame(report_data)
    
    # Add summary row
    if not df.empty:
        summary = {
            'vehicle_model': 'TOTAL',
            'weight_class': '-',
            'quantity': df['quantity'].sum(),
            'fleet_capex_premium': df['fleet_capex_premium'].sum(),
            'fleet_annual_savings': df['fleet_annual_savings'].sum(),
            'payback_years': df['payback_years'].mean(),
            'fleet_emissions_reduction': df['fleet_emissions_reduction'].sum(),
            '15yr_tco_savings': df['15yr_tco_savings'].sum(),
            '15yr_npv_savings': df['15yr_npv_savings'].sum()
        }
        df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
    
    return df


def generate_policy_recommendations(
    current_results: Dict[str, TCOResult],
    target_adoption_rate: float = 0.5
) -> List[Dict]:
    """
    Generate specific policy recommendations to achieve target adoption.
    
    Args:
        current_results: Current TCO results by vehicle ID
        target_adoption_rate: Target percentage of vehicles where BEV should be cheaper
        
    Returns:
        List of policy recommendation dicts
    """
    recommendations = []
    
    # Calculate current adoption potential
    competitive_count = 0
    gaps_by_class = defaultdict(list)
    
    for vehicle_id, tco_result in current_results.items():
        vehicle = BY_ID[vehicle_id]
        if vehicle.drivetrain_type == 'BEV' and vehicle.comparison_pair:
            diesel_tco = current_results.get(vehicle.comparison_pair)
            if diesel_tco:
                gap = tco_result.total_cost - diesel_tco.total_cost
                if gap < 0:
                    competitive_count += 1
                else:
                    gaps_by_class[vehicle.weight_class].append(gap)
    
    current_rate = competitive_count / len(gaps_by_class) if gaps_by_class else 1.0
    
    if current_rate < target_adoption_rate:
        # Calculate required reduction
        all_gaps = [gap for gaps in gaps_by_class.values() for gap in gaps]
        required_percentile = int((1 - target_adoption_rate) * 100)
        target_reduction = np.percentile(all_gaps, required_percentile) if all_gaps else 0
        
        # Generate recommendations by impact
        if target_reduction > 50000:
            recommendations.append({
                'priority': 'High',
                'measure': 'Purchase Rebate',
                'suggested_value': min(int(target_reduction * 0.4), 50000),
                'rationale': f'Direct reduction of ${target_reduction * 0.4:,.0f} addresses {required_percentile}% of gap'
            })
        
        if target_reduction > 20000:
            recommendations.append({
                'priority': 'High',
                'measure': 'Stamp Duty Exemption',
                'suggested_value': 1.0,
                'rationale': 'Full exemption provides ~3% purchase price reduction'
            })
        
        recommendations.append({
            'priority': 'Medium',
            'measure': 'Green Loan Subsidy',
            'suggested_value': 0.02,
            'rationale': '2% interest reduction saves ~$15,000 over financing term'
        })
        
        # Class-specific recommendations
        for weight_class, gaps in gaps_by_class.items():
            avg_gap = np.mean(gaps)
            if avg_gap > 30000:
                recommendations.append({
                    'priority': 'High',
                    'measure': f'{weight_class}-specific incentive',
                    'suggested_value': avg_gap * 0.5,
                    'rationale': f'Target support for {weight_class} segment with ${avg_gap:,.0f} average gap'
                })
    
    return recommendations