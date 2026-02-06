"""Tests for Pydantic models and validation rules."""

from __future__ import annotations

import pytest

from backend.app.models.calculation import CostBreakdown
from backend.app.models.session import DutyCyclePayload, WizardDataPayload


def test_duty_cycle_validation_enforces_total() -> None:
    with pytest.raises(ValueError, match="Duty cycle splits must sum to"):
        WizardDataPayload(
            current_vehicle="BEV001",
            comparison_vehicles=["DSL001"],
            scenario="baseline",
            purchase_method="outright",
            duty_cycle=DutyCyclePayload(urban=30, regional=30, long_haul=30),
        )


def test_duty_cycle_rounds_to_four_decimals() -> None:
    payload = DutyCyclePayload(urban=33.333333, regional=33.333333, long_haul=33.333334)
    assert payload.urban == 33.3333
    assert payload.regional == 33.3333
    assert payload.long_haul == 33.3333


def test_wizard_data_accepts_aliases() -> None:
    payload = WizardDataPayload.model_validate(
        {
            "currentVehicle": "BEV001",
            "comparisonVehicles": ["DSL001"],
            "scenario": "baseline",
            "purchaseMethod": "outright",
            "dutyCycle": {"urban": 30, "regional": 40, "longHaul": 30},
        }
    )
    assert payload.current_vehicle == "BEV001"
    assert payload.comparison_vehicles == ["DSL001"]


def test_cost_breakdown_migrates_legacy_flat_shape() -> None:
    legacy = {
        "purchase_cost": 100.0,
        "fuel_cost": 200.0,
        "maintenance_cost": 300.0,
        "insurance_cost": 400.0,
        "registration_cost": 500.0,
        "battery_replacement_cost": 600.0,
        "financing_cost": 700.0,
        "carbon_cost": 800.0,
        "charging_labour_cost": 900.0,
        "payload_penalty_cost": 1000.0,
        "residual_value": 1100.0,
        "depreciation": 1200.0,
        "taxes_and_fees": 1300.0,
    }

    breakdown = CostBreakdown.model_validate(legacy)

    assert breakdown.upfront_costs.purchase_cost == 100.0
    assert breakdown.npv_costs.fuel_cost == 200.0
    assert breakdown.nominal_costs.financing_cost == 700.0
