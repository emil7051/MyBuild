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
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    wizard_state: Mapped[dict | None] = mapped_column(JSON, default=dict)
    cached_results: Mapped[list | None] = mapped_column(JSON, default=list)
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
    __tablename__ = "user_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(16), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)
    purchase_method: Mapped[str] = mapped_column(String(16), nullable=False)
    overrides: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="inputs")


class CalculationResultRecord(Base):
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(16), nullable=False)
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
