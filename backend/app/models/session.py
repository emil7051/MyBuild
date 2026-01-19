"""Pydantic models for session persistence and analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.calculation import (
    CalculationResponse,
    CostOverride,
    VehicleParamOverride,
)


class DutyCyclePayload(BaseModel):
    urban: float = Field(ge=0, le=100)
    regional: float = Field(ge=0, le=100)
    long_haul: float = Field(ge=0, le=100, alias="longHaul")

    @field_validator("urban", "regional", "long_haul")
    @classmethod
    def _round_values(cls, value: float) -> float:  # noqa: D401
        """Ensure floats are rounded to two decimals for storage consistency."""

        return round(float(value), 4)

    def total(self) -> float:
        return self.urban + self.regional + self.long_haul

    model_config = {
        "populate_by_name": True,
    }


class WizardDataPayload(BaseModel):
    current_vehicle: Optional[str] = Field(default=None, alias="currentVehicle")
    comparison_vehicles: List[str] = Field(
        default_factory=list, alias="comparisonVehicles"
    )
    scenario: str
    purchase_method: Literal["financed", "outright"] = Field(alias="purchaseMethod")
    duty_cycle: DutyCyclePayload = Field(alias="dutyCycle")
    overrides: Optional[CostOverride] = None
    vehicle_param_overrides: Optional[Dict[str, VehicleParamOverride]] = Field(
        default=None, alias="vehicleParamOverrides"
    )

    model_config = {
        "populate_by_name": True,
    }

    @model_validator(mode="after")
    def _validate_duty_cycle(self) -> "WizardDataPayload":
        if abs(self.duty_cycle.total() - 100) > 0.5:
            raise ValueError("Duty cycle splits must sum to ~100%.")
        return self


class OperatorProfilePayload(BaseModel):
    operator_type: Optional[str] = Field(default=None, alias="operatorType")
    fleet_size: Optional[str] = Field(default=None, alias="fleetSize")
    contact_email: Optional[str] = Field(default=None, alias="contactEmail")
    consent_to_contact: bool = Field(default=False, alias="consentToContact")
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }


class FeedbackPayload(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None


class SessionPayloadBase(BaseModel):
    wizard_data: WizardDataPayload = Field(alias="wizardData")
    results: Optional[List[CalculationResponse]] = None
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None

    model_config = {
        "populate_by_name": True,
    }


class SessionCreate(SessionPayloadBase):
    pass


class SessionUpdate(BaseModel):
    wizard_data: Optional[WizardDataPayload] = Field(default=None, alias="wizardData")
    results: Optional[List[CalculationResponse]] = None
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None

    model_config = {
        "populate_by_name": True,
    }


class SessionResponse(BaseModel):
    session_id: str = Field(alias="sessionId")
    status: str
    wizard_data: WizardDataPayload = Field(alias="wizardData")
    results: List[CalculationResponse] = Field(default_factory=list)
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None
    updated_at: datetime = Field(alias="updatedAt")
    last_calculated_at: Optional[datetime] = Field(
        default=None, alias="lastCalculatedAt"
    )

    model_config = {
        "populate_by_name": True,
    }


class AnalyticsSummary(BaseModel):
    total_sessions: int = Field(alias="totalSessions")
    completed_sessions: int = Field(alias="completedSessions")
    calculations_last_24h: int = Field(alias="calculationsLast24h")
    bev_win_rate: Optional[float] = Field(default=None, alias="bevWinRate")
    average_payback_years: Optional[float] = Field(
        default=None, alias="averagePaybackYears"
    )
    average_cost_delta: Optional[float] = Field(default=None, alias="averageCostDelta")
    top_vehicles: Dict[str, int] = Field(default_factory=dict, alias="topVehicles")

    model_config = {
        "populate_by_name": True,
    }
