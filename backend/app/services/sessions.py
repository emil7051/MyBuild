"""Session persistence and analytics services.

See `docs/security-requirements.md` for persistence and analytics requirements.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

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
from data.scenarios import SCENARIOS
from data.vehicles import BY_ID

_SCENARIO_LABEL_TO_KEY = {
    scenario.name.casefold(): key for key, scenario in SCENARIOS.items()
}


def _normalize_scenario_identifier(value: str | None, fallback: str) -> str:
    """Normalize scenario labels/keys to canonical scenario keys."""
    if not value:
        return fallback

    normalized_value = value.strip()
    if normalized_value in SCENARIOS:
        return normalized_value

    return _SCENARIO_LABEL_TO_KEY.get(normalized_value.casefold(), fallback)


class SessionService:
    """Handles creation, updates, and analytics for calculation sessions."""

    async def create_session(
        self, db: AsyncSession, payload: SessionCreate
    ) -> tuple[SessionCreateResponse, str]:
        """Create a new session."""
        now = datetime.now(timezone.utc)
        session_secret = generate_session_secret()

        record = SessionRecord(
            status="completed" if payload.results else "draft",
            wizard_state=self._wizard_to_json(payload.wizard_data),
            cached_results=self._results_to_json(
                payload.results or [],
                payload.wizard_data.scenario,
            ),
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
        loaded_record = await self._fetch_session_with_related(db, record.id)
        response = self._build_response(loaded_record)
        await cache_session(
            loaded_record.id,
            response.model_dump(by_alias=True),
            loaded_record.session_secret_hash,
        )

        created = SessionCreateResponse.model_validate(
            response.model_dump(by_alias=True)
        )
        return created, session_secret

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
            record.cached_results = self._results_to_json(
                payload.results,
                resolved_wizard.scenario,
            )
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

        loaded_record = await self._fetch_session_with_related(db, session_id)
        response = self._build_response(loaded_record)
        await cache_session(
            session_id,
            response.model_dump(by_alias=True),
            loaded_record.session_secret_hash,
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

        record = await self._fetch_session_with_related(db, session_id)
        verify_session_secret(session_secret, record.session_secret_hash)

        response = self._build_response(record)
        await cache_session(
            session_id,
            response.model_dump(by_alias=True),
            record.session_secret_hash,
        )
        return response

    async def analytics_summary(self, db: AsyncSession) -> AnalyticsSummary:
        """Get analytics summary using SQL aggregation."""
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

        # BEV vs Diesel comparison metrics using aggregate SQL.
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
        """Compute BEV vs Diesel outcomes in a single aggregate query."""
        bev_pairs: list[tuple[str, str, float]] = []
        for bev_id, bev_vehicle in BY_ID.items():
            if bev_vehicle.drivetrain_type != "BEV":
                continue
            diesel_id = bev_vehicle.comparison_pair
            diesel_vehicle = BY_ID.get(diesel_id)
            if not diesel_vehicle:
                continue
            bev_pairs.append(
                (bev_id, diesel_id, bev_vehicle.msrp - diesel_vehicle.msrp)
            )

        if not bev_pairs:
            return None, None, None

        bev = aliased(CalculationResultRecord)
        diesel = aliased(CalculationResultRecord)

        diesel_lookup = case(
            {bev_id: diesel_id for bev_id, diesel_id, _ in bev_pairs},
            value=bev.vehicle_id,
            else_=None,
        )
        initial_gap_lookup = case(
            {bev_id: initial_gap for bev_id, _, initial_gap in bev_pairs},
            value=bev.vehicle_id,
            else_=None,
        )
        annual_savings = diesel.annual_cost - bev.annual_cost
        payback_expr = case(
            (annual_savings > 0, initial_gap_lookup / annual_savings),
            else_=None,
        )

        stmt = (
            select(
                func.count().label("comparisons"),
                func.sum(case((bev.total_cost < diesel.total_cost, 1), else_=0)).label(
                    "bev_wins"
                ),
                func.sum(diesel.total_cost - bev.total_cost).label("cost_delta_sum"),
                func.sum(payback_expr).label("payback_sum"),
                func.count(payback_expr).label("payback_count"),
            )
            .select_from(bev)
            .join(
                diesel,
                (bev.session_id == diesel.session_id)
                & (diesel.vehicle_id == diesel_lookup),
            )
            .where(bev.vehicle_id.in_([bev_id for bev_id, _, _ in bev_pairs]))
        )

        row = (await db.execute(stmt)).one()
        comparisons = row.comparisons or 0
        bev_wins = row.bev_wins or 0
        cost_delta_sum = row.cost_delta_sum or 0.0
        payback_sum = row.payback_sum or 0.0
        payback_count = row.payback_count or 0

        bev_win_rate = (bev_wins / comparisons) if comparisons else None
        avg_payback = (payback_sum / payback_count) if payback_count else None
        avg_cost_delta = (cost_delta_sum / comparisons) if comparisons else None
        return bev_win_rate, avg_payback, avg_cost_delta

    async def _fetch_session_with_related(
        self, db: AsyncSession, session_id: str
    ) -> SessionRecord:
        """Load session with related profile/feedback in one DB round trip."""
        stmt = (
            select(SessionRecord)
            .options(
                joinedload(SessionRecord.operator_profile),
                joinedload(SessionRecord.feedback_entries),
            )
            .where(SessionRecord.id == session_id)
        )
        record = (await db.execute(stmt)).unique().scalar_one_or_none()
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")
        return record

    def _build_response(self, record: SessionRecord) -> SessionResponse:
        wizard_data = WizardDataPayload.model_validate(record.wizard_state)
        results = []
        for stored_result in record.cached_results or []:
            normalized_result = dict(stored_result)
            normalized_result["scenario_name"] = _normalize_scenario_identifier(
                normalized_result.get("scenario_name"),
                wizard_data.scenario,
            )
            results.append(CalculationResponse.model_validate(normalized_result))

        feedback_record = None
        if record.feedback_entries:
            feedback_record = max(
                record.feedback_entries,
                key=lambda item: item.created_at,
            )

        operator_profile = (
            self._map_operator_profile(record.operator_profile)
            if record.operator_profile
            else None
        )
        feedback_payload = (
            self._map_feedback(feedback_record) if feedback_record else None
        )

        return SessionResponse(
            session_id=record.id,
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
        """Replace user inputs with normalized override shape."""
        await db.execute(
            delete(UserInputRecord).where(UserInputRecord.session_id == session_id)
        )

        vehicle_ids = self._unique_vehicle_ids(wizard_data)

        # Store cost overrides and vehicle param overrides separately.
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
            # Store normalized structure as {"cost": {...}, "vehicle": {...}}.
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
            scenario_key = _normalize_scenario_identifier(
                result.scenario_name,
                wizard_data.scenario,
            )
            serialized_result = result.model_dump(mode="json")
            serialized_result["scenario_name"] = scenario_key
            db.add(
                CalculationResultRecord(
                    session_id=session_id,
                    vehicle_id=result.vehicle_id,
                    scenario_name=scenario_key,
                    purchase_method=wizard_data.purchase_method,
                    result_payload=serialized_result,
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
    def _results_to_json(
        results: Iterable[CalculationResponse],
        fallback_scenario_key: str,
    ) -> List[dict]:
        normalized_results: List[dict] = []
        for result in results:
            serialized_result = result.model_dump(by_alias=True)
            serialized_result["scenario_name"] = _normalize_scenario_identifier(
                result.scenario_name,
                fallback_scenario_key,
            )
            normalized_results.append(serialized_result)
        return normalized_results

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
