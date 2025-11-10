"""Service that adapts the legacy Python engine to FastAPI responses."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha1
from typing import Dict, Iterable, Tuple

from backend.app.core.config import settings
from backend.app.models import (
    CalculationRequest,
    CalculationResponse,
    ComparisonRequest,
    CostBreakdown,
    VehicleParamOverride,
)
from calculations.calculations import TCOResult, calculate_tco_from_inputs
from calculations.inputs import VehicleInputs
from data.scenarios import SCENARIOS
from data.vehicles import BY_ID, VehicleModel


class CalculationService:
    """Thin wrapper that translates HTTP requests into engine invocations."""

    def __init__(self) -> None:
        self._result_cache: Dict[str, CalculationResponse] = {}

    def calculate(self, request: CalculationRequest) -> CalculationResponse:
        """Run a single calculation and map it to an API-ready payload."""

        structural_overrides = (
            request.vehicle_overrides.model_dump(exclude_none=True)
            if request.vehicle_overrides
            else None
        )
        cache_key = self._build_cache_key(
            request.vehicle_id,
            request.scenario_name,
            request.purchase_method,
            request.overrides.to_engine_overrides() if request.overrides else None,
            structural_overrides,
        )

        if settings.cache_results and cache_key in self._result_cache:
            return self._result_cache[cache_key]

        vehicle = self._get_vehicle(request.vehicle_id)
        if request.vehicle_overrides:
            vehicle = self._apply_vehicle_overrides(
                vehicle, request.vehicle_overrides
            )
        scenario = self._get_scenario(request.scenario_name)
        inputs = VehicleInputs(
            vehicle=vehicle,
            scenario=scenario,
            purchase_method=request.purchase_method,
            interest_rate_override=(
                request.vehicle_overrides.interest_rate_override
                if request.vehicle_overrides
                else None
            ),
            charging_time_hours_override=(
                request.vehicle_overrides.charging_time_hours_override
                if request.vehicle_overrides
                else None
            ),
        )
        overrides = (
            request.overrides.to_engine_overrides() if request.overrides else None
        )
        tco_result = calculate_tco_from_inputs(inputs, overrides)
        parsed = self._map_result(tco_result, scenario.name)

        if settings.cache_results:
            self._result_cache[cache_key] = parsed
        return parsed

    def compare(self, request: ComparisonRequest) -> Iterable[CalculationResponse]:
        """Calculate multiple vehicles under the same parameters."""

        for vehicle_id in request.vehicle_ids:
            single_request = CalculationRequest(
                vehicle_id=vehicle_id,
                scenario_name=request.scenario_name,
                purchase_method=request.purchase_method,
                overrides=request.overrides,
                vehicle_overrides=(
                    (request.vehicle_param_overrides or {}).get(vehicle_id)
                ),
            )
            yield self.calculate(single_request)

    def _get_vehicle(self, vehicle_id: str) -> VehicleModel:
        try:
            return BY_ID[vehicle_id]
        except KeyError as exc:  # pragma: no cover - FastAPI handles error translation
            raise KeyError(f"Unknown vehicle_id '{vehicle_id}'.") from exc

    def _get_scenario(self, scenario_name: str):
        try:
            return SCENARIOS[scenario_name]
        except KeyError as exc:  # pragma: no cover
            raise ValueError(
                f"Unknown scenario '{scenario_name}'. Available: {', '.join(SCENARIOS.keys())}."
            ) from exc

    @staticmethod
    def _map_result(result: TCOResult, scenario_name: str) -> CalculationResponse:
        breakdown = CostBreakdown(
            purchase_cost=result.purchase_cost,
            fuel_cost=result.fuel_cost,
            maintenance_cost=result.maintenance_cost,
            insurance_cost=result.insurance_cost,
            registration_cost=result.registration_cost,
            battery_replacement_cost=result.battery_replacement_cost,
            financing_cost=result.financing_cost,
            carbon_cost=result.carbon_cost,
            charging_labour_cost=result.charging_labour_cost,
            payload_penalty_cost=result.payload_penalty_cost,
            residual_value=result.residual_value,
            depreciation=result.depreciation,
            taxes_and_fees=result.taxes_and_fees,
        )
        return CalculationResponse(
            vehicle_id=result.vehicle_id,
            scenario_name=scenario_name,
            total_cost=result.total_cost,
            annual_cost=result.annual_cost,
            cost_per_km=result.cost_per_km,
            breakdown=breakdown,
        )

    @staticmethod
    def _build_cache_key(
        vehicle_id: str,
        scenario_name: str,
        purchase_method: str,
        overrides: Dict[str, float] | None,
        vehicle_overrides: Dict[str, float] | None,
    ) -> str:
        """Return a deterministic cache key for a calculation request."""

        override_items: Tuple[Tuple[str, float], ...] = tuple(
            sorted((overrides or {}).items())
        )
        structural_items: Tuple[Tuple[str, float], ...] = tuple(
            sorted((vehicle_overrides or {}).items())
        )
        key_raw = (
            f"{vehicle_id}:{scenario_name}:{purchase_method}:{override_items}:"
            f"{structural_items}"
        )
        return sha1(key_raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _apply_vehicle_overrides(
        base: VehicleModel, overrides: VehicleParamOverride
    ) -> VehicleModel:
        payload: Dict[str, float] = {}
        if overrides.msrp_override is not None:
            payload["msrp"] = overrides.msrp_override
        if overrides.payload_override is not None:
            payload["payload"] = overrides.payload_override
        if overrides.range_km_override is not None:
            payload["range_km"] = overrides.range_km_override
        if overrides.battery_capacity_kwh_override is not None:
            payload["battery_capacity_kwh"] = overrides.battery_capacity_kwh_override
        if overrides.kwh_per_km_override is not None:
            payload["kwh_per_km"] = overrides.kwh_per_km_override
        if overrides.litres_per_km_override is not None:
            payload["litres_per_km"] = overrides.litres_per_km_override
        if overrides.annual_registration_override is not None:
            payload["annual_registration"] = overrides.annual_registration_override

        if not payload:
            return base
        return replace(base, **payload)
