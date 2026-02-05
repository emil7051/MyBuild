"""Pydantic models for session persistence and analytics endpoints.

API-007: Server-side payload validation for vehicleId, scenario, email, length.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.calculation import (
    CalculationResponse,
    CostOverride,
    VehicleParamOverride,
)
from data.constants import DUTY_CYCLE_TOTAL_TOLERANCE
from data.scenarios import SCENARIOS

# Valid scenarios sourced from data/scenarios.py
VALID_SCENARIOS = set(SCENARIOS.keys())

# Email regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Maximum lengths for freeform text fields (API-007)
MAX_EMAIL_LENGTH = 255
MAX_NOTES_LENGTH = 2000
MAX_COMMENT_LENGTH = 1000
MAX_VEHICLE_ID_LENGTH = 32


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
    current_vehicle: Optional[str] = Field(
        default=None,
        alias="currentVehicle",
        max_length=MAX_VEHICLE_ID_LENGTH,
    )
    comparison_vehicles: List[str] = Field(
        default_factory=list, alias="comparisonVehicles"
    )
    scenario: str = Field(max_length=64)
    purchase_method: Literal["financed", "outright"] = Field(alias="purchaseMethod")
    duty_cycle: DutyCyclePayload = Field(alias="dutyCycle")
    overrides: Optional[CostOverride] = None
    vehicle_param_overrides: Optional[Dict[str, VehicleParamOverride]] = Field(
        default=None, alias="vehicleParamOverrides"
    )

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("comparison_vehicles")
    @classmethod
    def _validate_comparison_vehicles(cls, value: List[str]) -> List[str]:
        """Validate comparison vehicle IDs have reasonable length."""
        if len(value) > 10:
            raise ValueError("Maximum 10 comparison vehicles allowed.")
        for v in value:
            if len(v) > MAX_VEHICLE_ID_LENGTH:
                raise ValueError(
                    f"Vehicle ID too long (max {MAX_VEHICLE_ID_LENGTH} chars)."
                )
        return value

    @field_validator("scenario")
    @classmethod
    def _validate_scenario(cls, value: str) -> str:
        """Validate scenario against known scenarios (API-007)."""
        if value not in VALID_SCENARIOS:
            raise ValueError(
                f"Invalid scenario '{value}'. "
                f"Must be one of: {', '.join(sorted(VALID_SCENARIOS))}"
            )
        return value

    @model_validator(mode="after")
    def _validate_duty_cycle(self) -> "WizardDataPayload":
        if abs(self.duty_cycle.total() - 100) > DUTY_CYCLE_TOTAL_TOLERANCE:
            raise ValueError("Duty cycle splits must sum to ~100%.")
        return self

    @model_validator(mode="after")
    def _validate_vehicle_ids(self) -> "WizardDataPayload":
        """Validate vehicle IDs exist in the catalog (API-007).

        Import is deferred to avoid circular imports.
        """
        from data.vehicles import BY_ID

        all_vehicle_ids = []
        if self.current_vehicle:
            all_vehicle_ids.append(self.current_vehicle)
        all_vehicle_ids.extend(self.comparison_vehicles)

        invalid_ids = [vid for vid in all_vehicle_ids if vid not in BY_ID]
        if invalid_ids:
            raise ValueError(f"Unknown vehicle ID(s): {', '.join(invalid_ids)}")

        return self


class OperatorProfilePayload(BaseModel):
    """Operator profile with validated email and length-limited fields (API-007)."""

    operator_type: Optional[str] = Field(
        default=None,
        alias="operatorType",
        max_length=64,
    )
    fleet_size: Optional[str] = Field(
        default=None,
        alias="fleetSize",
        max_length=32,
    )
    contact_email: Optional[str] = Field(
        default=None,
        alias="contactEmail",
        max_length=MAX_EMAIL_LENGTH,
    )
    consent_to_contact: bool = Field(default=False, alias="consentToContact")
    notes: Optional[str] = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
    )

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("contact_email")
    @classmethod
    def _validate_email(cls, value: Optional[str]) -> Optional[str]:
        """Validate email format if provided (API-007)."""
        if value is None or value == "":
            return value
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email format.")
        return value


class FeedbackPayload(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=MAX_COMMENT_LENGTH)


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


class SessionCreateResponse(SessionResponse):
    """Response for session creation."""

    session_secret: str = Field(alias="sessionSecret")


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
