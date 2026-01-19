"""Factories for building test payloads and models."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from backend.app.models.calculation import (
    CalculationResponse,
    CostBreakdown,
    CostOverride,
    VehicleParamOverride,
)
from backend.app.models.session import (
    DutyCyclePayload,
    FeedbackPayload,
    OperatorProfilePayload,
    SessionCreate,
    SessionUpdate,
    WizardDataPayload,
)

BEV_VEHICLE_ID = "BEV001"
DIESEL_VEHICLE_ID = "DSL001"


def make_duty_cycle(
    urban: float = 30.0,
    regional: float = 40.0,
    long_haul: float = 30.0,
) -> DutyCyclePayload:
    return DutyCyclePayload(urban=urban, regional=regional, long_haul=long_haul)


def make_breakdown(
    purchase_cost: float = 150000.0,
    fuel_cost: float = 20000.0,
    maintenance_cost: float = 5000.0,
    insurance_cost: float = 3000.0,
    registration_cost: float = 1000.0,
    battery_replacement_cost: float = 0.0,
    financing_cost: float = 0.0,
    carbon_cost: float = 0.0,
    charging_labour_cost: float = 0.0,
    payload_penalty_cost: float = 0.0,
    residual_value: float = 20000.0,
    depreciation: float = 100000.0,
    taxes_and_fees: float = 2000.0,
) -> CostBreakdown:
    return CostBreakdown(
        purchase_cost=purchase_cost,
        fuel_cost=fuel_cost,
        maintenance_cost=maintenance_cost,
        insurance_cost=insurance_cost,
        registration_cost=registration_cost,
        battery_replacement_cost=battery_replacement_cost,
        financing_cost=financing_cost,
        carbon_cost=carbon_cost,
        charging_labour_cost=charging_labour_cost,
        payload_penalty_cost=payload_penalty_cost,
        residual_value=residual_value,
        depreciation=depreciation,
        taxes_and_fees=taxes_and_fees,
    )


def make_calculation_response(
    vehicle_id: str = BEV_VEHICLE_ID,
    scenario_name: str = "baseline",
    total_cost: float = 100000.0,
    annual_cost: float = 10000.0,
    cost_per_km: float = 1.0,
    purchase_cost: float = 150000.0,
) -> CalculationResponse:
    return CalculationResponse(
        vehicle_id=vehicle_id,
        scenario_name=scenario_name,
        total_cost=total_cost,
        annual_cost=annual_cost,
        cost_per_km=cost_per_km,
        breakdown=make_breakdown(purchase_cost=purchase_cost),
    )


def make_default_results() -> list[CalculationResponse]:
    return [
        make_calculation_response(
            vehicle_id=BEV_VEHICLE_ID,
            total_cost=100000.0,
            annual_cost=10000.0,
            cost_per_km=1.0,
            purchase_cost=150000.0,
        ),
        make_calculation_response(
            vehicle_id=DIESEL_VEHICLE_ID,
            total_cost=120000.0,
            annual_cost=12000.0,
            cost_per_km=1.2,
            purchase_cost=100000.0,
        ),
    ]


def make_wizard_data(
    current_vehicle: str = BEV_VEHICLE_ID,
    comparison_vehicles: Optional[Sequence[str]] = None,
    scenario: str = "baseline",
    purchase_method: str = "outright",
    duty_cycle: Optional[DutyCyclePayload] = None,
    overrides: Optional[CostOverride] = None,
    vehicle_param_overrides: Optional[dict[str, VehicleParamOverride]] = None,
) -> WizardDataPayload:
    return WizardDataPayload(
        current_vehicle=current_vehicle,
        comparison_vehicles=list(comparison_vehicles or [DIESEL_VEHICLE_ID]),
        scenario=scenario,
        purchase_method=purchase_method,
        duty_cycle=duty_cycle or make_duty_cycle(),
        overrides=overrides,
        vehicle_param_overrides=vehicle_param_overrides,
    )


def make_operator_profile() -> OperatorProfilePayload:
    return OperatorProfilePayload(
        operator_type="fleet",
        fleet_size="50-100",
        contact_email="ops@example.com",
        consent_to_contact=True,
        notes="Interested in BEV adoption.",
    )


def make_feedback() -> FeedbackPayload:
    return FeedbackPayload(rating=4, comment="Clear outputs.")


def make_session_create(
    wizard_data: Optional[WizardDataPayload] = None,
    results: Optional[Iterable[CalculationResponse]] = None,
    operator_profile: Optional[OperatorProfilePayload] = None,
    feedback: Optional[FeedbackPayload] = None,
) -> SessionCreate:
    return SessionCreate(
        wizard_data=wizard_data or make_wizard_data(),
        results=list(results) if results is not None else make_default_results(),
        operator_profile=operator_profile or make_operator_profile(),
        feedback=feedback or make_feedback(),
    )


def make_session_update(
    wizard_data: Optional[WizardDataPayload] = None,
    results: Optional[Iterable[CalculationResponse]] = None,
    operator_profile: Optional[OperatorProfilePayload] = None,
    feedback: Optional[FeedbackPayload] = None,
) -> SessionUpdate:
    return SessionUpdate(
        wizard_data=wizard_data,
        results=list(results) if results is not None else None,
        operator_profile=operator_profile,
        feedback=feedback,
    )


def make_session_payload_dict(**kwargs) -> dict:
    return make_session_create(**kwargs).model_dump(by_alias=True)


def make_session_update_payload_dict(**kwargs) -> dict:
    return make_session_update(**kwargs).model_dump(by_alias=True, exclude_none=True)
