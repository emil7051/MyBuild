"""Data validation helpers shared between tests and build pipelines."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.constants import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    VEHICLE_LIFE,
)
from data.scenarios import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    SCENARIOS,
    EconomicScenario,
)
from data.vehicles import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    ALL_MODELS,
    BY_ID,
    VehicleModel,
)


@dataclass
class ValidationReport:
    """Structured output returned by the validator."""

    vehicles: Dict[str, List[str]]
    scenarios: Dict[str, List[str]]
    comparison_pairs: List[str]
    is_valid: bool


class DataValidator:
    """Validates vehicle data, scenarios, and comparison pair integrity."""

    PAYLOAD_LIMITS: Dict[str, Tuple[float, float]] = {
        "Light Rigid": (0.5, 10.0),
        "Medium Rigid": (5.0, 30.0),
        "Articulated": (20.0, 75.0),
    }

    @classmethod
    def validate_vehicle(cls, vehicle: VehicleModel) -> List[str]:
        issues: List[str] = []

        if vehicle.msrp <= 0:
            issues.append(f"{vehicle.vehicle_id}: MSRP must be positive.")
        if vehicle.annual_kms <= 0:
            issues.append(f"{vehicle.vehicle_id}: Annual kms must be positive.")

        bounds = cls.PAYLOAD_LIMITS.get(vehicle.weight_class)
        if bounds:
            lower, upper = bounds
            if not (lower <= vehicle.payload <= upper):
                issues.append(
                    f"{vehicle.vehicle_id}: Payload outside expected range for {vehicle.weight_class} "
                    f"({lower}–{upper} t)."
                )

        if vehicle.drivetrain_type == "BEV" and vehicle.range_km > 0:
            expected = vehicle.battery_capacity_kwh / vehicle.range_km
            if vehicle.kwh_per_km <= 0:
                issues.append(f"{vehicle.vehicle_id}: kWh per km must be positive.")
            elif abs(vehicle.kwh_per_km - expected) / expected > 0.2:
                issues.append(
                    f"{vehicle.vehicle_id}: kWh per km inconsistent with capacity/range (expected ~{expected:.2f})."
                )

        if vehicle.drivetrain_type == "Diesel" and vehicle.litres_per_km <= 0:
            issues.append(f"{vehicle.vehicle_id}: Diesel consumption must be positive.")

        return issues

    @staticmethod
    def validate_scenario(scenario: EconomicScenario) -> List[str]:
        issues: List[str] = []

        trajectories = [
            ("diesel price trajectory", scenario.diesel_price_trajectory),
            ("electricity price trajectory", scenario.electricity_price_trajectory),
            ("battery price trajectory", scenario.battery_price_trajectory),
        ]
        for label, values in trajectories:
            if len(values) < VEHICLE_LIFE:
                issues.append(f"{scenario.name}: {label} shorter than vehicle life.")
            if any(value < 0 for value in values):
                issues.append(
                    f"{scenario.name}: {label} contains negative multipliers."
                )

        return issues

    @staticmethod
    def validate_comparison_pairs() -> List[str]:
        issues: List[str] = []
        for vehicle in ALL_MODELS:
            pair_id = vehicle.comparison_pair
            counterpart = BY_ID.get(pair_id)
            if not counterpart:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' missing."
                )
                continue
            if counterpart.comparison_pair != vehicle.vehicle_id:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' does not point back to this vehicle."
                )
            if counterpart.weight_class != vehicle.weight_class:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' weight class mismatch ({counterpart.weight_class})."
                )
        return issues

    @classmethod
    def validate_all(cls) -> ValidationReport:
        vehicle_issues = {
            vehicle.vehicle_id: issues
            for vehicle in ALL_MODELS
            if (issues := cls.validate_vehicle(vehicle))
        }
        scenario_issues = {
            name: issues
            for name, scenario in SCENARIOS.items()
            if (issues := cls.validate_scenario(scenario))
        }
        comparison_issues = cls.validate_comparison_pairs()

        return ValidationReport(
            vehicles=vehicle_issues,
            scenarios=scenario_issues,
            comparison_pairs=comparison_issues,
            is_valid=not (vehicle_issues or scenario_issues or comparison_issues),
        )


def _print_dict_issues(title: str, issues: Dict[str, List[str]]) -> None:
    if not issues:
        return
    print(f"\n{title}:")
    for key in sorted(issues):
        for message in issues[key]:
            print(f"  - {key}: {message}")


def _print_list_issues(title: str, issues: List[str]) -> None:
    if not issues:
        return
    print(f"\n{title}:")
    for message in issues:
        print(f"  - {message}")


def main() -> None:
    """CLI entry point for validating data tables."""

    report = DataValidator.validate_all()
    total_vehicles = len(ALL_MODELS)
    total_scenarios = len(SCENARIOS)

    if report.is_valid:
        print(
            f"Data validation passed for {total_vehicles} vehicles and {total_scenarios} scenarios."
        )
        return

    print("Data validation FAILED. See details below.")
    _print_dict_issues("Vehicle issues", report.vehicles)
    _print_dict_issues("Scenario issues", report.scenarios)
    _print_list_issues("Comparison pair issues", report.comparison_pairs)
    sys.exit(1)


if __name__ == "__main__":
    main()
