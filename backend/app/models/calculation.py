"""Schema definitions for calculation requests and responses."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CostOverride(BaseModel):
    """Optional override hooks that align with the shared TypeScript calculator inputs."""

    annual_kms_variation: Optional[float] = Field(
        default=None,
        description="Absolute kilometres per year to use instead of the vehicle default.",
    )
    residual_value_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to the discounted residual value (e.g. 0.9).",
    )
    fuel_price_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to diesel fuel price trajectory (1.05 = +5%).",
    )
    electricity_price_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to electricity price trajectory (0.95 = -5%).",
    )
    maintenance_cost_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to maintenance trajectory (1.1 = +10%).",
    )
    battery_life_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to BEV battery life simulations (0.7 = shorter life).",
    )
    charging_efficiency_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to BEV charging efficiency (1.1 = worse efficiency).",
    )

    model_config = {
        "extra": "forbid",
    }

    def to_engine_overrides(self) -> Dict[str, float]:
        """Return the overrides dictionary understood by the Python engine."""

        payload: Dict[str, float] = {}
        if self.annual_kms_variation is not None:
            payload["annual_kms_variation"] = self.annual_kms_variation
        if self.residual_value_variation is not None:
            payload["residual_value_variation"] = self.residual_value_variation
        if self.fuel_price_variation is not None:
            payload["fuel_price_variation"] = self.fuel_price_variation
        if self.electricity_price_variation is not None:
            payload["electricity_price_variation"] = self.electricity_price_variation
        if self.maintenance_cost_variation is not None:
            payload["maintenance_cost_variation"] = self.maintenance_cost_variation
        if self.battery_life_variation is not None:
            payload["battery_life_variation"] = self.battery_life_variation
        if self.charging_efficiency_variation is not None:
            payload["charging_efficiency_variation"] = (
                self.charging_efficiency_variation
            )
        return payload


class VehicleParamOverride(BaseModel):
    """Optional per-vehicle structural overrides."""

    msrp_override: Optional[float] = Field(default=None)
    payload_override: Optional[float] = Field(default=None)
    range_km_override: Optional[float] = Field(default=None)
    battery_capacity_kwh_override: Optional[float] = Field(default=None)
    kwh_per_km_override: Optional[float] = Field(default=None)
    litres_per_km_override: Optional[float] = Field(default=None)
    annual_registration_override: Optional[float] = Field(default=None)
    interest_rate_override: Optional[float] = Field(default=None)
    charging_time_hours_override: Optional[float] = Field(default=None)

    model_config = {
        "extra": "forbid",
    }


class CalculationRequest(BaseModel):
    """Request payload for a single TCO calculation."""

    vehicle_id: str = Field(..., description="Vehicle identifier, e.g. BEV001.")
    scenario_name: str = Field(
        default="baseline", description="Scenario key from data.scenarios."
    )
    purchase_method: Literal["financed", "outright"] = Field(default="financed")
    overrides: Optional[CostOverride] = None
    vehicle_overrides: Optional[VehicleParamOverride] = Field(
        default=None, description="Optional structural overrides for this vehicle."
    )


class ComparisonRequest(BaseModel):
    """Request payload for comparing a list of vehicles under the same scenario."""

    vehicle_ids: List[str] = Field(..., min_length=1)
    scenario_name: str = Field(default="baseline")
    purchase_method: Literal["financed", "outright"] = Field(default="financed")
    overrides: Optional[CostOverride] = None
    vehicle_param_overrides: Optional[Dict[str, VehicleParamOverride]] = Field(
        default=None,
        description="Map of vehicle_id -> overrides applied when present.",
    )


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
