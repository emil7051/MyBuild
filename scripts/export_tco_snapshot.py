#!/usr/bin/env python3
"""Emit Python TCO results so the TypeScript parity harness can compare against them."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Callable, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from calculations.calculations import (  # noqa: E402  # Needs repo root on sys.path
    TCOResult,
    calculate_tco_from_inputs,
)
from calculations.inputs import vehicle_data  # noqa: E402
from data.scenarios import SCENARIOS  # noqa: E402
from data.vehicles import ALL_MODELS, VehicleModel  # noqa: E402

PurchaseMethod = str  # Literal['financed', 'outright'] but kept simple here
OverrideBuilder = Callable[[VehicleModel], Optional[Dict[str, float]]]

PURCHASE_METHODS: tuple[PurchaseMethod, PurchaseMethod] = ("financed", "outright")


def base_override(_: VehicleModel) -> Optional[Dict[str, float]]:
    return None


def stress_override(vehicle: VehicleModel) -> Dict[str, float]:
    return {
        "annual_kms_variation": vehicle.annual_kms * 1.1,
        "fuel_price_variation": 1.15,
        "electricity_price_variation": 0.9,
        "maintenance_cost_variation": 1.1,
        "residual_value_variation": 0.85,
        "battery_life_variation": 0.75,
        "charging_efficiency_variation": 0.95,
    }


OVERRIDE_CASES: Dict[str, OverrideBuilder] = {
    "baseline": base_override,
    "stress_test": stress_override,
}


def result_to_payload(result: TCOResult) -> Dict[str, float]:
    return {
        "vehicle_id": result.vehicle_id,
        "scenario_name": result.scenario_name,
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
            "taxes_and_fees": result.taxes_and_fees,
        },
    }


def build_case_snapshot(
    builder: OverrideBuilder,
) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    case_results: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    for method in PURCHASE_METHODS:
        method_results: Dict[str, Dict[str, Dict[str, float]]] = {}
        for scenario_key, scenario in SCENARIOS.items():
            scenario_results: Dict[str, Dict[str, float]] = {}
            for vehicle in ALL_MODELS:
                overrides = builder(vehicle)
                inputs = vehicle_data.get_vehicle(vehicle.vehicle_id, scenario, method)
                result = calculate_tco_from_inputs(inputs, overrides)
                scenario_results[vehicle.vehicle_id] = result_to_payload(result)
            method_results[scenario_key] = scenario_results
        case_results[method] = method_results
    return case_results


def build_override_map(builder: OverrideBuilder) -> Dict[str, Dict[str, float]]:
    overrides: Dict[str, Dict[str, float]] = {}
    for vehicle in ALL_MODELS:
        override_payload = builder(vehicle)
        if override_payload:
            overrides[vehicle.vehicle_id] = override_payload
    return overrides


def main() -> None:
    payload = {
        case_name: {
            "results": build_case_snapshot(case_builder),
            "overrides": build_override_map(case_builder),
        }
        for case_name, case_builder in OVERRIDE_CASES.items()
    }
    json.dump({"cases": payload}, sys.stdout)


if __name__ == "__main__":
    main()
