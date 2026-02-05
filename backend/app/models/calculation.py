"""Schema definitions for calculation requests and responses.

SEC-003: Backend bounds checking aligned with frontend Zod validation
(frontend/src/forms/wizardForm.ts) to prevent invalid values from
non-UI clients or corrupted persisted state.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from data.constants import OVERRIDE_LIMITS

COST_LIMITS = OVERRIDE_LIMITS["cost"]
VEHICLE_LIMITS = OVERRIDE_LIMITS["vehicle"]


class CostOverride(BaseModel):
    """Optional override hooks that align with shared TypeScript calculator inputs.

    All multiplier fields are constrained to match frontend validation ranges
    to ensure consistent behavior across API clients (SEC-003).
    """

    annual_kms_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["annual_kms_variation"]["min"],
        le=COST_LIMITS["annual_kms_variation"]["max"],
        description="Absolute kilometres per year (5,000–250,000).",
    )
    residual_value_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["residual_value_variation"]["min"],
        le=COST_LIMITS["residual_value_variation"]["max"],
        description="Multiplier applied to the discounted residual value (0.5–1.5).",
    )
    fuel_price_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["fuel_price_variation"]["min"],
        le=COST_LIMITS["fuel_price_variation"]["max"],
        description="Multiplier applied to diesel fuel price trajectory (0.5–2.0).",
    )
    electricity_price_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["electricity_price_variation"]["min"],
        le=COST_LIMITS["electricity_price_variation"]["max"],
        description="Multiplier applied to electricity price trajectory (0.5–2.0).",
    )
    maintenance_cost_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["maintenance_cost_variation"]["min"],
        le=COST_LIMITS["maintenance_cost_variation"]["max"],
        description="Multiplier applied to maintenance trajectory (0.5–1.5).",
    )
    battery_life_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["battery_life_variation"]["min"],
        le=COST_LIMITS["battery_life_variation"]["max"],
        description="Multiplier applied to BEV battery life simulations (0.5–1.5).",
    )
    charging_efficiency_variation: Optional[float] = Field(
        default=None,
        ge=COST_LIMITS["charging_efficiency_variation"]["min"],
        le=COST_LIMITS["charging_efficiency_variation"]["max"],
        description="Multiplier applied to BEV charging efficiency (0.7–1.3).",
    )

    model_config = {
        "extra": "forbid",
    }


class VehicleParamOverride(BaseModel):
    """Optional per-vehicle structural overrides.

    Bounds aligned with frontend Zod validation (SEC-003). Values outside
    these ranges will be rejected with 422 validation errors.
    """

    msrp_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["msrp_override"]["min"],
        le=VEHICLE_LIMITS["msrp_override"]["max"],
        description="Vehicle MSRP override (0–$10M).",
    )
    payload_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["payload_override"]["min"],
        le=VEHICLE_LIMITS["payload_override"]["max"],
        description="Payload capacity override (0–100 tonnes).",
    )
    range_km_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["range_km_override"]["min"],
        le=VEHICLE_LIMITS["range_km_override"]["max"],
        description="Range override (50–2500 km). Minimum prevents division by zero.",
    )
    battery_capacity_kwh_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["battery_capacity_kwh_override"]["min"],
        le=VEHICLE_LIMITS["battery_capacity_kwh_override"]["max"],
        description="Battery capacity override (0–2000 kWh).",
    )
    kwh_per_km_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["kwh_per_km_override"]["min"],
        le=VEHICLE_LIMITS["kwh_per_km_override"]["max"],
        description="Energy consumption (0.1–10 kWh/km). Min prevents div by zero.",
    )
    litres_per_km_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["litres_per_km_override"]["min"],
        le=VEHICLE_LIMITS["litres_per_km_override"]["max"],
        description="Fuel consumption (0.05–5 L/km). Min prevents div by zero.",
    )
    annual_registration_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["annual_registration_override"]["min"],
        le=VEHICLE_LIMITS["annual_registration_override"]["max"],
        description="Annual registration cost override (0–$100k).",
    )
    interest_rate_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["interest_rate_override"]["min"],
        le=VEHICLE_LIMITS["interest_rate_override"]["max"],
        description="Interest rate override as decimal (0–0.2, i.e., 0–20%).",
    )
    charging_time_hours_override: Optional[float] = Field(
        default=None,
        ge=VEHICLE_LIMITS["charging_time_hours_override"]["min"],
        le=VEHICLE_LIMITS["charging_time_hours_override"]["max"],
        description="Charging time (0.1–8 hours). Min prevents div by zero.",
    )

    model_config = {
        "extra": "forbid",
    }


class CostBreakdown(BaseModel):
    purchase_cost: float
    fuel_cost: float
    maintenance_cost: float
    insurance_cost: float
    registration_cost: float
    battery_replacement_cost: float
    financing_cost: float
    carbon_cost: float
    charging_labour_cost: float
    payload_penalty_cost: float
    residual_value: float
    depreciation: float
    taxes_and_fees: float


class CalculationResponse(BaseModel):
    """Response payload summarising key metrics from the shared calculator."""

    vehicle_id: str
    scenario_name: str
    total_cost: float
    annual_cost: float
    cost_per_km: float
    breakdown: CostBreakdown
