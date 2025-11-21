import json
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations.calculations import calculate_tco_from_inputs
from calculations.inputs import vehicle_data
from data.scenarios import SCENARIOS

def generate_verification_data():
    verification_data = []
    
    # Test cases configuration
    scenarios_to_test = ["baseline", "high_fuel_price"]
    purchase_methods = ["financed", "outright"]
    
    # 1. Standard cases for all vehicles
    print("Generating standard cases...")
    for vehicle_id in vehicle_data.get_all_vehicles():
        for scenario_name in scenarios_to_test:
            if scenario_name not in SCENARIOS:
                continue
                
            scenario = SCENARIOS[scenario_name]
            
            for purchase_method in purchase_methods:
                vehicle_inputs = vehicle_data.get_vehicle(
                    vehicle_id, scenario, purchase_method
                )
                
                result = calculate_tco_from_inputs(vehicle_inputs)
                
                case = {
                    "id": f"{vehicle_id}-{scenario_name}-{purchase_method}",
                    "input": {
                        "vehicle_id": vehicle_id,
                        "scenario_name": scenario_name,
                        "purchase_method": purchase_method,
                        "overrides": None,
                        "vehicle_overrides": None
                    },
                    "expected": {
                        "total_cost": result.total_cost,
                        "annual_cost": result.annual_cost,
                        "cost_per_km": result.cost_per_km,
                        "breakdown": {
                            "purchase_cost": result.purchase_cost,
                            "fuel_cost": result.fuel_cost,
                            "maintenance_cost": result.maintenance_cost,
                            "insurance_cost": result.insurance_cost,
                            "registration_cost": result.registration_cost,
                            "battery_replacement_cost": result.battery_replacement_cost,
                            "financing_cost": result.financing_cost,
                            "carbon_cost": result.carbon_cost,
                            "charging_labour_cost": result.charging_labour_cost,
                            "payload_penalty_cost": result.payload_penalty_cost,
                            "residual_value": result.residual_value,
                            "depreciation": result.depreciation,
                            "taxes_and_fees": result.taxes_and_fees
                        }
                    }
                }
                verification_data.append(case)

    # 2. Override cases (sample vehicle)
    print("Generating override cases...")
    sample_vehicle = "BEV_LIGHT_TRUCK" # Assuming this ID exists, will verify
    if sample_vehicle not in vehicle_data.get_all_vehicles():
        sample_vehicle = list(vehicle_data.get_all_vehicles().keys())[0]
        
    overrides_config = {
        "annual_kms_variation": 50000.0,
        "fuel_price_variation": 1.5,
        "electricity_price_variation": 0.8
    }
    
    vehicle_inputs = vehicle_data.get_vehicle(sample_vehicle, SCENARIOS["baseline"], "financed")
    result = calculate_tco_from_inputs(vehicle_inputs, overrides=overrides_config)
    
    case = {
        "id": f"{sample_vehicle}-overrides",
        "input": {
            "vehicle_id": sample_vehicle,
            "scenario_name": "baseline",
            "purchase_method": "financed",
            "overrides": overrides_config,
            "vehicle_overrides": None
        },
        "expected": {
            "total_cost": result.total_cost,
            "annual_cost": result.annual_cost,
            "cost_per_km": result.cost_per_km,
            "breakdown": {
                "purchase_cost": result.purchase_cost,
                "fuel_cost": result.fuel_cost,
                "maintenance_cost": result.maintenance_cost,
                "insurance_cost": result.insurance_cost,
                "registration_cost": result.registration_cost,
                "battery_replacement_cost": result.battery_replacement_cost,
                "financing_cost": result.financing_cost,
                "carbon_cost": result.carbon_cost,
                "charging_labour_cost": result.charging_labour_cost,
                "payload_penalty_cost": result.payload_penalty_cost,
                "residual_value": result.residual_value,
                "depreciation": result.depreciation,
                "taxes_and_fees": result.taxes_and_fees
            }
        }
    }
    verification_data.append(case)

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), "../frontend/src/test/verification_data.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(verification_data, f, indent=2)
    
    print(f"Generated {len(verification_data)} test cases to {output_path}")

if __name__ == "__main__":
    generate_verification_data()
