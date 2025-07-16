"""
Generates and saves TCO component comparison visualisations.
"""
import os
import sys
import pandas as pd
from typing import List, Dict, Tuple

# Add project root to Python path to allow for correct module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculations.calculations import calculate_tco_from_inputs, TCOResult
from calculations.inputs import vehicle_data, VehicleInputs
from data.vehicles import BY_ID, VehicleModel
from output.visualisations import TCOVisualiser
import data.constants as const
from calculations.utils import calculate_annualised_cost


# Create output directory if it doesn't exist
OUTPUT_DIR = 'output/charts'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_paired_charts():
    """Generates comparison charts for each BEV/Diesel pair."""
    print("Generating paired vehicle comparison charts...")
    
    pairs_inputs: List[Tuple[VehicleInputs, VehicleInputs]] = vehicle_data.get_vehicle_pairs()

    for bev_inputs, diesel_inputs in pairs_inputs:
        bev_tco = calculate_tco_from_inputs(bev_inputs)
        diesel_tco = calculate_tco_from_inputs(diesel_inputs)
        
        pair_name = f"{bev_inputs.vehicle.model_name}_vs_{diesel_inputs.vehicle.model_name}"

        # Cost per km chart
        cost_per_km_fig = TCOVisualiser.create_cost_per_km_chart(
            [bev_tco, diesel_tco],
            title=f"Cost per km: {pair_name.replace('_', ' ')}"
        )
        cost_per_km_fig.write_html(f"{OUTPUT_DIR}/{pair_name}_cost_per_km.html")

        # Waterfall charts
        bev_waterfall_fig_with_infra = TCOVisualiser.create_tco_waterfall_chart(
            bev_tco, 
            bev_inputs,
            title=f"TCO Waterfall (with Infrastructure): {bev_inputs.vehicle.model_name} (BEV)",
            include_infrastructure=True
        )
        bev_waterfall_fig_with_infra.write_html(f"{OUTPUT_DIR}/{bev_inputs.vehicle.vehicle_id}_waterfall_with_infra.html")

        bev_waterfall_fig_no_infra = TCOVisualiser.create_tco_waterfall_chart(
            bev_tco, 
            bev_inputs,
            title=f"TCO Waterfall (no Infrastructure): {bev_inputs.vehicle.model_name} (BEV)",
            include_infrastructure=False
        )
        bev_waterfall_fig_no_infra.write_html(f"{OUTPUT_DIR}/{bev_inputs.vehicle.vehicle_id}_waterfall_no_infra.html")

        diesel_waterfall_fig = TCOVisualiser.create_tco_waterfall_chart(
            diesel_tco,
            diesel_inputs,
            title=f"TCO Waterfall: {diesel_inputs.vehicle.model_name} (Diesel)"
        )
        diesel_waterfall_fig.write_html(f"{OUTPUT_DIR}/{diesel_inputs.vehicle.vehicle_id}_waterfall.html")
        
    print(f"Paired charts generated in {OUTPUT_DIR}/")

def generate_class_average_charts():
    """Generates comparison charts for averaged vehicle classes."""
    print("Generating class average comparison charts...")
    
    all_inputs = vehicle_data.get_all_vehicles()
    all_tcos = {vid: calculate_tco_from_inputs(v_inputs) for vid, v_inputs in all_inputs.items()}
    
    df_data = []
    for vehicle_id, tco_result in all_tcos.items():
        vehicle = BY_ID[vehicle_id]
        record = tco_result.__dict__
        record['weight_class'] = vehicle.weight_class
        record['drivetrain_type'] = vehicle.drivetrain_type
        record['annual_kms'] = vehicle.annual_kms
        df_data.append(record)
    
    df = pd.DataFrame(df_data)

    # Calculate average cost components per km
    def get_avg_cost_per_km(group):
        # Annualise total NPV costs for each component, then divide by total kms
        total_kms = group['annual_kms'].sum()
        avg_depreciation_km = calculate_annualised_cost(group['depreciation'].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE) / total_kms
        avg_fuel_km = calculate_annualised_cost(group['fuel_cost'].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE) / total_kms
        avg_maintenance_km = calculate_annualised_cost(group['maintenance_cost'].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE) / total_kms
        return pd.Series({
            'Depreciation': avg_depreciation_km,
            'Fuel': avg_fuel_km,
            'Maintenance': avg_maintenance_km
        })

    avg_costs_df = df.groupby(['weight_class', 'drivetrain_type']).apply(get_avg_cost_per_km).reset_index()

    # Plot
    for weight_class in ['Light Rigid', 'Medium Rigid', 'Articulated']:
        chart_data = avg_costs_df[avg_costs_df['weight_class'] == weight_class]
        
        if not chart_data.empty:
            fig = TCOVisualiser.create_cost_per_km_chart_from_avg(
                chart_data,
                title=f"Average Cost per km: {weight_class}"
            )
            fig.write_html(f"{OUTPUT_DIR}/AVG_{weight_class.replace(' ', '_')}_cost_per_km.html")

    print(f"Class average charts generated in {OUTPUT_DIR}/")


def generate_comparison_csv():
    """Generates a CSV file with detailed TCO comparison data."""
    print("Generating comparison CSV file...")

    all_inputs = vehicle_data.get_all_vehicles()
    
    csv_data = []

    for vehicle_id, inputs in all_inputs.items():
        result = calculate_tco_from_inputs(inputs)
        vehicle = BY_ID[vehicle_id]

        # Cost per km components (annualised)
        annual_kms = vehicle.annual_kms
        depreciation_per_km = calculate_annualised_cost(result.depreciation, const.VEHICLE_LIFE, const.DISCOUNT_RATE) / annual_kms
        fuel_per_km = calculate_annualised_cost(result.fuel_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE) / annual_kms
        maintenance_per_km = calculate_annualised_cost(result.maintenance_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE) / annual_kms

        # Waterfall components (undiscounted)
        initial_cost = inputs.initial_cost
        residual_value = inputs.get_residual_value(const.VEHICLE_LIFE)
        fuel_cost_undiscounted = sum(inputs.get_fuel_cost_year(y) for y in range(1, const.VEHICLE_LIFE + 1))
        maintenance_undiscounted = sum(inputs.get_maintenance_cost_year(y) for y in range(1, const.VEHICLE_LIFE + 1))
        insurance_undiscounted = inputs.annual_insurance_cost * const.VEHICLE_LIFE
        registration_undiscounted = inputs.vehicle.annual_registration * const.VEHICLE_LIFE
        taxes_and_fees_undiscounted = inputs.stamp_duty + registration_undiscounted
        infrastructure_cost = const.CHARGER_COST if vehicle.drivetrain_type == 'BEV' else 0

        record = {
            'vehicle_id': vehicle.vehicle_id,
            'model_name': vehicle.model_name,
            'drivetrain_type': vehicle.drivetrain_type,
            'weight_class': vehicle.weight_class,
            'comparison_pair_id': vehicle.comparison_pair,
            
            # Key TCO metrics
            'total_tco_npv': result.total_cost,
            'annual_tco': result.annual_cost,
            'cost_per_km': result.cost_per_km,

            # Cost per km breakdown
            'cost_km_depreciation': depreciation_per_km,
            'cost_km_fuel': fuel_per_km,
            'cost_km_maintenance': maintenance_per_km,

            # Waterfall components (undiscounted)
            'wfall_asset_cost': initial_cost,
            'wfall_residual_value': -residual_value, # show as negative
            'wfall_fuel': fuel_cost_undiscounted,
            'wfall_maintenance': maintenance_undiscounted,
            'wfall_insurance': insurance_undiscounted,
            'wfall_taxes_fees': taxes_and_fees_undiscounted,
            'wfall_infrastructure': infrastructure_cost,
        }
        csv_data.append(record)

    df = pd.DataFrame(csv_data)
    
    # Add comparison pair name for easier filtering in Excel
    pair_map = df.set_index('vehicle_id')['model_name'].to_dict()
    df['comparison_pair_name'] = df['comparison_pair_id'].map(pair_map)
    
    # Reorder columns for clarity
    column_order = [
        'vehicle_id', 'model_name', 'drivetrain_type', 'weight_class', 'comparison_pair_id', 'comparison_pair_name',
        'total_tco_npv', 'annual_tco', 'cost_per_km',
        'cost_km_depreciation', 'cost_km_fuel', 'cost_km_maintenance',
        'wfall_asset_cost', 'wfall_residual_value', 'wfall_fuel', 'wfall_maintenance', 
        'wfall_infrastructure', 'wfall_insurance', 'wfall_taxes_fees'
    ]
    df = df[column_order]
    
    # Also add the class average data
    avg_data = []
    for (weight_class, drivetrain), group in df.groupby(['weight_class', 'drivetrain_type']):
        avg_record = group.mean(numeric_only=True).to_dict()
        avg_record['vehicle_id'] = f"AVG_{weight_class}_{drivetrain}".replace(' ', '_')
        avg_record['model_name'] = f"Average {weight_class} {drivetrain}"
        avg_record['drivetrain_type'] = drivetrain
        avg_record['weight_class'] = weight_class
        avg_record['comparison_pair_id'] = ''
        avg_record['comparison_pair_name'] = ''
        avg_data.append(avg_record)

    avg_df = pd.DataFrame(avg_data)
    
    # Combine individual and average data
    final_df = pd.concat([df, avg_df], ignore_index=True)

    csv_path = os.path.join(OUTPUT_DIR, 'tco_comparison_data.csv')
    final_df.to_csv(csv_path, index=False)
    print(f"Comparison data saved to {csv_path}")

if __name__ == '__main__':
    generate_paired_charts()
    generate_class_average_charts()
    generate_comparison_csv()
    print("All comparison charts and data have been generated.") 