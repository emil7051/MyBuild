"""Schemas that expose vehicle metadata to consumers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VehicleSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    vehicle_id: str
    model_name: str
    drivetrain_type: str
    weight_class: str
    comparison_pair: str


class VehicleDetail(VehicleSummary):
    payload: float
    msrp: float
    range_km: float
    battery_capacity_kwh: float
    kwh_per_km: float
    litres_per_km: float
    maintenance_cost_per_km: float
    annual_registration: float
    annual_kms: float
