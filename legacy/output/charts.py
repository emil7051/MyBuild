"""
Generates and saves TCO component comparison visualisations.
"""

import os
import sys
from typing import List, Tuple

import pandas as pd

# Add project root to Python path to allow for correct module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from output.visualisations import TCOVisualiser

import data.constants as const
from calculations.calculations import calculate_tco_from_inputs
from calculations.inputs import VehicleInputs, vehicle_data
from calculations.utils import (
    calculate_annualised_cost,
    calculate_npv_of_payments,
    calculate_present_value,
)
from data.vehicles import BY_ID

# Create output directory if it doesn't exist
OUTPUT_DIR = "output/charts"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def generate_paired_charts():
    """Generates comparison charts for each BEV/Diesel pair."""
    print("Generating paired vehicle comparison charts...")

    pairs_inputs: List[Tuple[VehicleInputs, VehicleInputs]] = (
        vehicle_data.get_vehicle_pairs()
    )

    for bev_inputs, diesel_inputs in pairs_inputs:
        bev_tco = calculate_tco_from_inputs(bev_inputs)
        diesel_tco = calculate_tco_from_inputs(diesel_inputs)

        pair_name = (
            f"{bev_inputs.vehicle.model_name}_vs_{diesel_inputs.vehicle.model_name}"
        )

        # Cost per km chart
        cost_per_km_fig = TCOVisualiser.create_cost_per_km_chart(
            [bev_tco, diesel_tco], title=f"Cost per km: {pair_name.replace('_', ' ')}"
        )
        cost_per_km_fig.write_html(f"{OUTPUT_DIR}/{pair_name}_cost_per_km.html")

        # Waterfall charts
        bev_waterfall_fig_with_infra = TCOVisualiser.create_tco_waterfall_chart(
            bev_tco,
            bev_inputs,
            title=f"TCO Waterfall (with Infrastructure): {bev_inputs.vehicle.model_name} (BEV)",
            include_infrastructure=True,
        )
        bev_waterfall_fig_with_infra.write_html(
            f"{OUTPUT_DIR}/{bev_inputs.vehicle.vehicle_id}_waterfall_with_infra.html"
        )

        bev_waterfall_fig_no_infra = TCOVisualiser.create_tco_waterfall_chart(
            bev_tco,
            bev_inputs,
            title=f"TCO Waterfall (no Infrastructure): {bev_inputs.vehicle.model_name} (BEV)",
            include_infrastructure=False,
        )
        bev_waterfall_fig_no_infra.write_html(
            f"{OUTPUT_DIR}/{bev_inputs.vehicle.vehicle_id}_waterfall_no_infra.html"
        )

        diesel_waterfall_fig = TCOVisualiser.create_tco_waterfall_chart(
            diesel_tco,
            diesel_inputs,
            title=f"TCO Waterfall: {diesel_inputs.vehicle.model_name} (Diesel)",
        )
        diesel_waterfall_fig.write_html(
            f"{OUTPUT_DIR}/{diesel_inputs.vehicle.vehicle_id}_waterfall.html"
        )

    print(f"Paired charts generated in {OUTPUT_DIR}/")


def generate_class_average_charts():
    """Generates comparison charts for averaged vehicle classes."""
    print("Generating class average comparison charts...")

    all_inputs = vehicle_data.get_all_vehicles()
    all_tcos = {
        vid: calculate_tco_from_inputs(v_inputs) for vid, v_inputs in all_inputs.items()
    }

    df_data = []
    for vehicle_id, tco_result in all_tcos.items():
        vehicle = BY_ID[vehicle_id]
        record = tco_result.__dict__
        record["weight_class"] = vehicle.weight_class
        record["drivetrain_type"] = vehicle.drivetrain_type
        record["annual_kms"] = vehicle.annual_kms
        df_data.append(record)

    df = pd.DataFrame(df_data)

    # Calculate average cost components per km
    def get_avg_cost_per_km(group):
        # Annualise total NPV costs for each component, then divide by total kms
        total_kms = group["annual_kms"].sum()
        avg_depreciation_km = (
            calculate_annualised_cost(
                group["depreciation"].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / total_kms
        )
        avg_fuel_km = (
            calculate_annualised_cost(
                group["fuel_cost"].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / total_kms
        )
        avg_maintenance_km = (
            calculate_annualised_cost(
                group["maintenance_cost"].sum(), const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / total_kms
        )
        return pd.Series(
            {
                "Depreciation": avg_depreciation_km,
                "Fuel": avg_fuel_km,
                "Maintenance": avg_maintenance_km,
            }
        )

    avg_costs_df = (
        df.groupby(["weight_class", "drivetrain_type"])
        .apply(get_avg_cost_per_km)
        .reset_index()
    )

    # Plot
    for weight_class in ["Light Rigid", "Medium Rigid", "Articulated"]:
        chart_data = avg_costs_df[avg_costs_df["weight_class"] == weight_class]

        if not chart_data.empty:
            fig = TCOVisualiser.create_cost_per_km_chart_from_avg(
                chart_data, title=f"Average Cost per km: {weight_class}"
            )
            fig.write_html(
                f"{OUTPUT_DIR}/AVG_{weight_class.replace(' ', '_')}_cost_per_km.html"
            )

    print(f"Class average charts generated in {OUTPUT_DIR}/")


def generate_comparison_csv():
    """Generates a CSV file with detailed TCO comparison data."""
    print("Generating comparison CSV file...")

    all_inputs = vehicle_data.get_all_vehicles()

    csv_data = []

    for vehicle_id, inputs in all_inputs.items():
        result = calculate_tco_from_inputs(inputs)
        vehicle = BY_ID[vehicle_id]

        # --- Re-calculate NPVs for consistency ---
        # NPV of purchase payments (aligns with TCO calculation)
        if inputs.purchase_method == "outright":
            npv_purchase_payments = inputs.initial_cost
        else:
            npv_down_payment = inputs.down_payment
            num_payments = const.FINANCING_TERM * 12
            npv_monthly_payments = calculate_npv_of_payments(
                inputs.monthly_payment, num_payments, const.DISCOUNT_RATE
            )
            npv_purchase_payments = npv_down_payment + npv_monthly_payments

        # PV of fixed costs (aligns with TCO calculation)
        total_insurance_pv = calculate_present_value(
            inputs.annual_insurance_cost, const.VEHICLE_LIFE
        )
        total_registration_pv = calculate_present_value(
            inputs.vehicle.annual_registration, const.VEHICLE_LIFE
        )

        # --- Annualised Cost Per KM (from discounted cash flows) ---
        annual_kms = vehicle.annual_kms

        # Capital cost = purchase payments less residual value
        capital_cost_pv = npv_purchase_payments - result.residual_value
        capital_cost_per_km = (
            calculate_annualised_cost(
                capital_cost_pv, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )

        # Operating costs (from TCOResult NPVs)
        fuel_per_km = (
            calculate_annualised_cost(
                result.fuel_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        maintenance_per_km = (
            calculate_annualised_cost(
                result.maintenance_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        insurance_per_km = (
            calculate_annualised_cost(
                total_insurance_pv, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        registration_per_km = (
            calculate_annualised_cost(
                total_registration_pv, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        carbon_per_km = (
            calculate_annualised_cost(
                result.carbon_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        battery_per_km = (
            calculate_annualised_cost(
                result.battery_replacement_cost, const.VEHICLE_LIFE, const.DISCOUNT_RATE
            )
            / annual_kms
        )
        penalties_per_km = (
            calculate_annualised_cost(
                result.payload_penalty_cost + result.charging_labour_cost,
                const.VEHICLE_LIFE,
                const.DISCOUNT_RATE,
            )
            / annual_kms
        )

        record = {
            "vehicle_id": vehicle.vehicle_id,
            "model_name": vehicle.model_name,
            "drivetrain_type": vehicle.drivetrain_type,
            "weight_class": vehicle.weight_class,
            "comparison_pair_id": vehicle.comparison_pair,
            # Key TCO metrics
            "total_tco_npv": result.total_cost,
            "annual_tco": result.annual_cost,
            "cost_per_km_total": result.cost_per_km,
            # Cost per km breakdown (all annualised from NPVs)
            "cost_km_capital": capital_cost_per_km,
            "cost_km_fuel": fuel_per_km,
            "cost_km_maintenance": maintenance_per_km,
            "cost_km_insurance": insurance_per_km,
            "cost_km_registration": registration_per_km,
            "cost_km_carbon": carbon_per_km,
            "cost_km_battery": battery_per_km,
            "cost_km_penalties": penalties_per_km,
        }
        csv_data.append(record)

    df = pd.DataFrame(csv_data)

    # Add comparison pair name for easier filtering in Excel
    pair_map = df.set_index("vehicle_id")["model_name"].to_dict()
    df["comparison_pair_name"] = df["comparison_pair_id"].map(pair_map)

    # Reorder columns for clarity
    column_order = [
        "vehicle_id",
        "model_name",
        "drivetrain_type",
        "weight_class",
        "comparison_pair_id",
        "comparison_pair_name",
        "total_tco_npv",
        "annual_tco",
        "cost_per_km_total",
        "cost_km_capital",
        "cost_km_fuel",
        "cost_km_maintenance",
        "cost_km_insurance",
        "cost_km_registration",
        "cost_km_carbon",
        "cost_km_battery",
        "cost_km_penalties",
    ]
    df = df[column_order]

    # Also add the class average data
    avg_data = []
    for (weight_class, drivetrain), group in df.groupby(
        ["weight_class", "drivetrain_type"]
    ):
        avg_record = group.mean(numeric_only=True).to_dict()
        avg_record["vehicle_id"] = f"AVG_{weight_class}_{drivetrain}".replace(" ", "_")
        avg_record["model_name"] = f"Average {weight_class} {drivetrain}"
        avg_record["drivetrain_type"] = drivetrain
        avg_record["weight_class"] = weight_class
        avg_record["comparison_pair_id"] = ""
        avg_record["comparison_pair_name"] = ""
        avg_data.append(avg_record)

    avg_df = pd.DataFrame(avg_data)

    # Combine individual and average data
    final_df = pd.concat([df, avg_df], ignore_index=True)

    csv_path = os.path.join(OUTPUT_DIR, "tco_comparison_data_v2.csv")
    final_df.to_csv(csv_path, index=False)
    print(f"Comparison data saved to {csv_path}")


def generate_waterfall_data_csv():
    """Generates a CSV file with the data for all waterfall charts."""
    print("Generating waterfall chart data CSV...")

    all_inputs = vehicle_data.get_all_vehicles()

    waterfall_data = []

    for vehicle_id, inputs in all_inputs.items():
        result = calculate_tco_from_inputs(inputs)
        vehicle = BY_ID[vehicle_id]

        # Calculate common components
        initial_cost = inputs.initial_cost
        residual_value_pv = result.residual_value
        fuel_cost_npv = result.fuel_cost
        maintenance_npv = result.maintenance_cost
        insurance_pv = calculate_present_value(
            inputs.annual_insurance_cost, const.VEHICLE_LIFE
        )
        registration_pv = calculate_present_value(
            inputs.vehicle.annual_registration, const.VEHICLE_LIFE
        )
        taxes_and_fees_pv = inputs.stamp_duty + registration_pv
        penalties_npv = result.payload_penalty_cost + result.charging_labour_cost

        base_components = {
            "Asset Cost": initial_cost,
            "Residual Value (PV)": -residual_value_pv,
            "Fuel (NPV)": fuel_cost_npv,
            "Maintenance (NPV)": maintenance_npv,
            "Insurance (PV)": insurance_pv,
            "Taxes & Fees (PV)": taxes_and_fees_pv,
            "Payload/Charging Penalties (NPV)": penalties_npv,
        }

        if vehicle.drivetrain_type == "BEV":
            # With infrastructure
            components_with_infra = base_components.copy()
            components_with_infra["Infrastructure"] = const.CHARGER_COST
            for component, value in components_with_infra.items():
                waterfall_data.append(
                    {
                        "vehicle_id": vehicle.vehicle_id,
                        "model_name": vehicle.model_name,
                        "drivetrain_type": vehicle.drivetrain_type,
                        "chart_type": "with_infra",
                        "cost_component": component,
                        "value": value,
                    }
                )

            # Without infrastructure
            components_no_infra = base_components.copy()
            for component, value in components_no_infra.items():
                waterfall_data.append(
                    {
                        "vehicle_id": vehicle.vehicle_id,
                        "model_name": vehicle.model_name,
                        "drivetrain_type": vehicle.drivetrain_type,
                        "chart_type": "no_infra",
                        "cost_component": component,
                        "value": value,
                    }
                )

        else:  # Diesel
            components_diesel = base_components.copy()
            for component, value in components_diesel.items():
                waterfall_data.append(
                    {
                        "vehicle_id": vehicle.vehicle_id,
                        "model_name": vehicle.model_name,
                        "drivetrain_type": vehicle.drivetrain_type,
                        "chart_type": "diesel",
                        "cost_component": component,
                        "value": value,
                    }
                )

    df = pd.DataFrame(waterfall_data)

    # Add a 'total' row for each chart group
    total_rows = []
    for (vid, chart_type), group in df.groupby(["vehicle_id", "chart_type"]):
        total_value = group["value"].sum()
        vehicle = BY_ID[vid]
        total_rows.append(
            {
                "vehicle_id": vid,
                "model_name": vehicle.model_name,
                "drivetrain_type": vehicle.drivetrain_type,
                "chart_type": chart_type,
                "cost_component": "Final TCO (NPV)",
                "value": total_value,
            }
        )

    total_df = pd.DataFrame(total_rows)
    final_df = pd.concat([df, total_df], ignore_index=True)

    # Reorder for better readability
    final_df = final_df.sort_values(by=["vehicle_id", "chart_type"]).reset_index(
        drop=True
    )

    csv_path = os.path.join(OUTPUT_DIR, "waterfall_chart_data.csv")
    final_df.to_csv(csv_path, index=False)
    print(f"Waterfall chart data saved to {csv_path}")


def generate_all_charts():
    """Generates all charts."""
    generate_paired_charts()
    generate_class_average_charts()


def generate_all_csv():
    """Generates all CSVs."""
    generate_comparison_csv()
    generate_waterfall_data_csv()
