"""Database table definitions for session persistence and analytics."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class SessionRecord(Base):
    """Session record with wizard state and optional access control secret.

    The session_secret_hash column is retained for potential future access
    control but is not enforced by current session flows.
    """

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_created_at", "created_at"),
        Index("ix_sessions_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    wizard_state: Mapped[dict | None] = mapped_column(JSON, default=dict)
    cached_results: Mapped[list | None] = mapped_column(JSON, default=list)
    # Bcrypt hash of session access secret reserved for optional PII protection
    session_secret_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="Bcrypt hash of session access secret"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    inputs: Mapped[list["UserInputRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    results: Mapped[list["CalculationResultRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    operator_profile: Mapped["OperatorProfileRecord"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    feedback_entries: Mapped[list["FeedbackRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class UserInputRecord(Base):
    """User input record storing vehicle selection and overrides per session."""

    __tablename__ = "user_inputs"
    __table_args__ = (
        Index("ix_user_inputs_session_id", "session_id"),
        Index("ix_user_inputs_vehicle_id", "vehicle_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(32), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)
    purchase_method: Mapped[str] = mapped_column(String(16), nullable=False)
    overrides: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="inputs")


class CalculationResultRecord(Base):
    """Calculation result record storing TCO analysis outcomes per session/vehicle."""

    __tablename__ = "calculation_results"
    __table_args__ = (
        Index("ix_calculation_results_session_id", "session_id"),
        Index("ix_calculation_results_vehicle_id", "vehicle_id"),
        Index("ix_calculation_results_created_at", "created_at"),
        # Composite index for analytics aggregation queries
        Index(
            "ix_calculation_results_analytics",
            "session_id",
            "vehicle_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(32), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)
    purchase_method: Mapped[str] = mapped_column(String(16), nullable=False)
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    annual_cost: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="results")


class OperatorProfileRecord(Base):
    __tablename__ = "operator_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    operator_type: Mapped[str | None] = mapped_column(String(64))
    fleet_size: Mapped[str | None] = mapped_column(String(32))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    consent_to_contact: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="operator_profile")


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="feedback_entries")
