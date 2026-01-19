"""Tests for Pydantic models and validation rules."""

from __future__ import annotations

import pytest

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
