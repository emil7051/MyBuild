"""Service objects that expose read-only vehicle metadata."""

from __future__ import annotations

from typing import Dict, List

from backend.app.models import VehicleDetail, VehicleSummary
from data.vehicles import ALL_MODELS, BY_ID, VehicleModel


class VehicleCatalogService:
    """Provides lookup helpers for vehicle metadata."""

    def __init__(self) -> None:
        self._vehicles: Dict[str, VehicleModel] = BY_ID

    def list_summaries(self) -> List[VehicleSummary]:
        return [self._to_summary(model) for model in ALL_MODELS]

    def get(self, vehicle_id: str) -> VehicleDetail:
        try:
            model = self._vehicles[vehicle_id]
        except KeyError as exc:
            raise KeyError(f"Unknown vehicle_id '{vehicle_id}'.") from exc
        return self._to_detail(model)

    @staticmethod
    def _to_summary(model: VehicleModel) -> VehicleSummary:
        return VehicleSummary(
            vehicle_id=model.vehicle_id,
            model_name=model.model_name,
            drivetrain_type=model.drivetrain_type,
            weight_class=model.weight_class,
            comparison_pair=model.comparison_pair,
        )

    @staticmethod
    def _to_detail(model: VehicleModel) -> VehicleDetail:
        return VehicleDetail(
            vehicle_id=model.vehicle_id,
            model_name=model.model_name,
            drivetrain_type=model.drivetrain_type,
            weight_class=model.weight_class,
            comparison_pair=model.comparison_pair,
            payload=model.payload,
            msrp=model.msrp,
            range_km=model.range_km,
            battery_capacity_kwh=model.battery_capacity_kwh,
            kwh_per_km=model.kwh_per_km,
            litres_per_km=model.litres_per_km,
            annual_registration=model.annual_registration,
            annual_kms=model.annual_kms,
        )
