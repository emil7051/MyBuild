"""Session persistence and analytics services.

API-003: Override shape normalization for consistent storage.
API-006: SQL-optimized analytics aggregation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.cache import cache_session, get_cached_session
from backend.app.core.security import (
    generate_session_secret,
    hash_secret,
    verify_session_secret,
)
from backend.app.db.models import (
    CalculationResultRecord,
    FeedbackRecord,
    OperatorProfileRecord,
    SessionRecord,
    UserInputRecord,
)
from backend.app.models.calculation import CalculationResponse
from backend.app.models.session import (
    AnalyticsSummary,
    FeedbackPayload,
    OperatorProfilePayload,
    SessionCreate,
    SessionCreateResponse,
    SessionResponse,
    SessionUpdate,
    WizardDataPayload,
)
from data.vehicles import BY_ID


class SessionService:
    """Handles creation, updates, and analytics for calculation sessions."""

    async def create_session(
        self, db: AsyncSession, payload: SessionCreate
    ) -> SessionCreateResponse:
        """Create a new session."""
        now = datetime.now(timezone.utc)
        session_secret = generate_session_secret()

        record = SessionRecord(
            status="completed" if payload.results else "draft",
            wizard_state=self._wizard_to_json(payload.wizard_data),
            cached_results=self._results_to_json(payload.results or []),
            last_calculated_at=now if payload.results else None,
            session_secret_hash=hash_secret(session_secret),
        )
        db.add(record)
        await db.flush()

        await self._replace_inputs(db, record.id, payload.wizard_data)
        if payload.results:
            await self._replace_results(
                db, record.id, payload.results, payload.wizard_data
            )
        if payload.operator_profile:
            await self._upsert_operator_profile(db, record.id, payload.operator_profile)
        if payload.feedback:
            await self._insert_feedback(db, record.id, payload.feedback)

        await db.commit()
        await db.refresh(record)

        response = await self._build_response(db, record.id)
        await cache_session(
            record.id,
            response.model_dump(by_alias=True),
            record.session_secret_hash,
        )

        create_payload = response.model_dump(by_alias=True)
        create_payload["sessionSecret"] = session_secret
        return SessionCreateResponse.model_validate(create_payload)

    async def update_session(
        self,
        db: AsyncSession,
        session_id: str,
        payload: SessionUpdate,
        session_secret: str | None = None,
    ) -> SessionResponse:
        """Update an existing session."""
        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")
        verify_session_secret(session_secret, record.session_secret_hash)

        if payload.wizard_data:
            record.wizard_state = self._wizard_to_json(payload.wizard_data)
            await self._replace_inputs(db, session_id, payload.wizard_data)

        resolved_wizard = payload.wizard_data or WizardDataPayload.model_validate(
            record.wizard_state
        )

        if payload.results is not None:
            record.cached_results = self._results_to_json(payload.results)
            if payload.results:
                record.status = "completed"
                record.last_calculated_at = datetime.now(timezone.utc)
                await self._replace_results(
                    db, session_id, payload.results, resolved_wizard
                )
            else:
                record.status = "draft"
                record.last_calculated_at = None
                await self._clear_results(db, session_id)

        if payload.operator_profile is not None:
            await self._upsert_operator_profile(
                db, session_id, payload.operator_profile
            )

        if payload.feedback:
            await self._insert_feedback(db, session_id, payload.feedback)

        await db.commit()

        response = await self._build_response(db, session_id)
        await cache_session(
            session_id,
            response.model_dump(by_alias=True),
            record.session_secret_hash,
        )
        return response

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
        session_secret: str | None = None,
    ) -> SessionResponse:
        """Retrieve a session."""
        cached = await get_cached_session(session_id)
        if cached:
            verify_session_secret(session_secret, cached["session_secret_hash"])
            return SessionResponse.model_validate(cached["payload"])

        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")
        verify_session_secret(session_secret, record.session_secret_hash)

        await db.refresh(record)

        response = await self._build_response(db, session_id)
        await cache_session(
            session_id,
            response.model_dump(by_alias=True),
            record.session_secret_hash,
        )
        return response

    async def analytics_summary(self, db: AsyncSession) -> AnalyticsSummary:
        """Get analytics summary using SQL aggregation (API-006)."""
        # Basic session counts
        total_sessions = await db.scalar(select(func.count(SessionRecord.id))) or 0
        completed_sessions = (
            await db.scalar(
                select(func.count(SessionRecord.id)).where(
                    SessionRecord.status == "completed"
                )
            )
        ) or 0

        # Calculations in last 24h
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        calculations_last_24h = (
            await db.scalar(
                select(func.count(CalculationResultRecord.id)).where(
                    CalculationResultRecord.created_at >= cutoff
                )
            )
        ) or 0

        # Top vehicles (SQL aggregation)
        top_rows = await db.execute(
            select(
                CalculationResultRecord.vehicle_id,
                func.count(CalculationResultRecord.id).label("runs"),
            )
            .group_by(CalculationResultRecord.vehicle_id)
            .order_by(func.count(CalculationResultRecord.id).desc())
            .limit(5)
        )
        top_vehicles = {vehicle_id: runs for vehicle_id, runs in top_rows.all()}

        # BEV vs Diesel comparison metrics (API-006: SQL optimization)
        # For this we still need to fetch results but we can be more efficient
        (
            bev_win_rate,
            avg_payback,
            avg_cost_delta,
        ) = await self._compute_outcomes_optimized(db)

        return AnalyticsSummary(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            calculations_last_24h=calculations_last_24h,
            bev_win_rate=bev_win_rate,
            average_payback_years=avg_payback,
            average_cost_delta=avg_cost_delta,
            top_vehicles=top_vehicles,
        )

    async def _compute_outcomes_optimized(
        self, db: AsyncSession
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Compute BEV vs Diesel outcomes with optimized queries (API-006).

        Uses separate queries for aggregation to minimize memory usage.
        """
        # Get BEV vehicle IDs and their diesel comparison pairs
        bev_vehicles = {
            vid: v.comparison_pair
            for vid, v in BY_ID.items()
            if v.drivetrain_type == "BEV"
        }

        if not bev_vehicles:
            return None, None, None

        # Fetch only the columns we need (no full result_payload)
        rows = await db.execute(
            select(
                CalculationResultRecord.session_id,
                CalculationResultRecord.vehicle_id,
                CalculationResultRecord.total_cost,
                CalculationResultRecord.annual_cost,
            )
        )

        session_map: Dict[str, Dict[str, dict]] = defaultdict(dict)
        for row in rows.all():
            session_map[row.session_id][row.vehicle_id] = {
                "total_cost": row.total_cost,
                "annual_cost": row.annual_cost,
            }

        bev_wins = 0
        comparisons = 0
        cost_deltas: List[float] = []
        payback_values: List[float] = []

        # For payback, we need purchase costs - fetch only when needed
        for session_id, vehicles in session_map.items():
            for bev_id, diesel_id in bev_vehicles.items():
                if bev_id not in vehicles or diesel_id not in vehicles:
                    continue

                bev_data = vehicles[bev_id]
                diesel_data = vehicles[diesel_id]

                comparisons += 1
                if bev_data["total_cost"] < diesel_data["total_cost"]:
                    bev_wins += 1

                cost_deltas.append(diesel_data["total_cost"] - bev_data["total_cost"])

                # Estimate payback from annual savings
                annual_savings = diesel_data["annual_cost"] - bev_data["annual_cost"]
                if annual_savings > 0:
                    # Use average BEV premium as rough estimate
                    # This avoids loading full payloads
                    bev_vehicle = BY_ID.get(bev_id)
                    diesel_vehicle = BY_ID.get(diesel_id)
                    if bev_vehicle and diesel_vehicle:
                        initial_gap = bev_vehicle.msrp - diesel_vehicle.msrp
                        payback = max(initial_gap / annual_savings, 0)
                        payback_values.append(payback)

        bev_win_rate = (bev_wins / comparisons) if comparisons else None
        avg_payback = (
            sum(payback_values) / len(payback_values) if payback_values else None
        )
        avg_cost_delta = sum(cost_deltas) / len(cost_deltas) if cost_deltas else None
        return bev_win_rate, avg_payback, avg_cost_delta

    async def _build_response(
        self, db: AsyncSession, session_id: str
    ) -> SessionResponse:
        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")
        await db.refresh(record)

        wizard_data = WizardDataPayload.model_validate(record.wizard_state)
        results = [
            CalculationResponse.model_validate(result)
            for result in (record.cached_results or [])
        ]

        operator_profile_record = await db.scalar(
            select(OperatorProfileRecord).where(
                OperatorProfileRecord.session_id == session_id
            )
        )
        feedback_record = await db.scalars(
            select(FeedbackRecord)
            .where(FeedbackRecord.session_id == session_id)
            .order_by(FeedbackRecord.created_at.desc())
            .limit(1)
        )
        feedback = feedback_record.first()

        operator_profile = (
            self._map_operator_profile(operator_profile_record)
            if operator_profile_record
            else None
        )
        feedback_payload = self._map_feedback(feedback) if feedback else None

        return SessionResponse(
            session_id=session_id,
            status=record.status,
            wizard_data=wizard_data,
            results=results,
            operator_profile=operator_profile,
            feedback=feedback_payload,
            updated_at=record.updated_at,
            last_calculated_at=record.last_calculated_at,
        )

    async def _replace_inputs(
        self, db: AsyncSession, session_id: str, wizard_data: WizardDataPayload
    ) -> None:
        """Replace user inputs with normalized override shape (API-003)."""
        await db.execute(
            delete(UserInputRecord).where(UserInputRecord.session_id == session_id)
        )

        vehicle_ids = self._unique_vehicle_ids(wizard_data)

        # Normalize overrides shape (API-003)
        # Store cost overrides and vehicle param overrides separately for clarity
        shared_cost_overrides = (
            wizard_data.overrides.model_dump(exclude_none=True)
            if wizard_data.overrides
            else None
        )
        per_vehicle_overrides = (
            {
                vehicle_id: override.model_dump(exclude_none=True)
                for vehicle_id, override in wizard_data.vehicle_param_overrides.items()
            }
            if wizard_data.vehicle_param_overrides
            else {}
        )

        for vehicle_id in vehicle_ids:
            # Normalize override structure (API-003):
            # Store as { "cost": {...}, "vehicle": {...} } for consistency
            combined_overrides: Optional[dict] = None
            vehicle_specific = per_vehicle_overrides.get(vehicle_id)

            if shared_cost_overrides or vehicle_specific:
                combined_overrides = {}
                if shared_cost_overrides:
                    combined_overrides["cost"] = shared_cost_overrides
                if vehicle_specific:
                    combined_overrides["vehicle"] = vehicle_specific

            db.add(
                UserInputRecord(
                    session_id=session_id,
                    vehicle_id=vehicle_id,
                    scenario_name=wizard_data.scenario,
                    purchase_method=wizard_data.purchase_method,
                    overrides=combined_overrides,
                )
            )

    async def _replace_results(
        self,
        db: AsyncSession,
        session_id: str,
        results: Iterable[CalculationResponse],
        wizard_data: WizardDataPayload,
    ) -> None:
        await db.execute(
            delete(CalculationResultRecord).where(
                CalculationResultRecord.session_id == session_id
            )
        )
        for result in results:
            db.add(
                CalculationResultRecord(
                    session_id=session_id,
                    vehicle_id=result.vehicle_id,
                    scenario_name=result.scenario_name,
                    purchase_method=wizard_data.purchase_method,
                    result_payload=result.model_dump(mode="json"),
                    total_cost=result.total_cost,
                    annual_cost=result.annual_cost,
                    cost_per_km=result.cost_per_km,
                )
            )

    async def _clear_results(self, db: AsyncSession, session_id: str) -> None:
        await db.execute(
            delete(CalculationResultRecord).where(
                CalculationResultRecord.session_id == session_id
            )
        )

    async def _upsert_operator_profile(
        self, db: AsyncSession, session_id: str, payload: OperatorProfilePayload
    ) -> None:
        await db.execute(
            delete(OperatorProfileRecord).where(
                OperatorProfileRecord.session_id == session_id
            )
        )
        db.add(
            OperatorProfileRecord(
                session_id=session_id,
                operator_type=payload.operator_type,
                fleet_size=payload.fleet_size,
                contact_email=payload.contact_email,
                consent_to_contact=payload.consent_to_contact,
                notes=payload.notes,
            )
        )

    async def _insert_feedback(
        self, db: AsyncSession, session_id: str, payload: FeedbackPayload
    ) -> None:
        db.add(
            FeedbackRecord(
                session_id=session_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        )

    @staticmethod
    def _wizard_to_json(payload: WizardDataPayload) -> dict:
        return payload.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def _results_to_json(results: Iterable[CalculationResponse]) -> List[dict]:
        return [result.model_dump(by_alias=True) for result in results]

    @staticmethod
    def _unique_vehicle_ids(wizard_data: WizardDataPayload) -> List[str]:
        vehicles: List[str] = []
        if wizard_data.current_vehicle:
            vehicles.append(wizard_data.current_vehicle)
        vehicles.extend(wizard_data.comparison_vehicles)
        deduped = []
        for vehicle in vehicles:
            if vehicle and vehicle not in deduped:
                deduped.append(vehicle)
        return deduped

    @staticmethod
    def _map_operator_profile(record: OperatorProfileRecord) -> OperatorProfilePayload:
        return OperatorProfilePayload(
            operator_type=record.operator_type,
            fleet_size=record.fleet_size,
            contact_email=record.contact_email,
            consent_to_contact=record.consent_to_contact,
            notes=record.notes,
        )

    @staticmethod
    def _map_feedback(record: FeedbackRecord) -> FeedbackPayload:
        return FeedbackPayload(rating=record.rating, comment=record.comment)
