"""Versioned API router that wires endpoints to services.

API-002: UUID validation for session_id path parameters.
SEC-007: Analytics endpoint restricted to backend-only access via API key.
SEC-008: Rate limiting for session, analytics, and vehicle catalog endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import (
    get_rate_limit_analytics,
    get_rate_limit_sessions,
    get_rate_limit_vehicles,
    limiter,
    verify_analytics_api_key,
)
from backend.app.db.session import get_db_session
from backend.app.models import VehicleDetail, VehicleSummary
from backend.app.models.session import (
    AnalyticsSummary,
    SessionCreate,
    SessionCreateResponse,
    SessionResponse,
    SessionUpdate,
)
from backend.app.services import VehicleCatalogService
from backend.app.services.sessions import SessionService

api_router = APIRouter(prefix=settings.api_v1_prefix)

_vehicle_service = VehicleCatalogService()
_session_service = SessionService()


def validate_uuid(session_id: str) -> str:
    """Validate session_id is a valid UUID format (API-002).

    Raises HTTPException 422 for invalid UUIDs.
    """
    try:
        UUID(session_id, version=4)
        return session_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid session_id format. Expected UUID, got: {session_id}",
        )


@api_router.get("/health", tags=["system"])
def healthcheck():
    return {"status": "ok", "environment": settings.environment}


@api_router.get("/vehicles", response_model=List[VehicleSummary], tags=["vehicles"])
@limiter.limit(get_rate_limit_vehicles)
def list_vehicles(request: Request) -> List[VehicleSummary]:
    return _vehicle_service.list_summaries()


@api_router.get(
    "/vehicles/{vehicle_id}", response_model=VehicleDetail, tags=["vehicles"]
)
@limiter.limit(get_rate_limit_vehicles)
def get_vehicle(request: Request, vehicle_id: str) -> VehicleDetail:
    try:
        return _vehicle_service.get(vehicle_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["sessions"],
)
@limiter.limit(get_rate_limit_sessions)
async def create_session(
    request: Request,
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db_session),
) -> SessionCreateResponse:
    """Create a new session.

    Returns the session data for persistence and resume.
    """
    try:
        return await _session_service.create_session(db, payload)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.put(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
@limiter.limit(get_rate_limit_sessions)
async def update_session(
    request: Request,
    session_id: str,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Update an existing session.
    """
    # Validate UUID format (API-002)
    validate_uuid(session_id)

    try:
        return await _session_service.update_session(db, session_id, payload)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
@limiter.limit(get_rate_limit_sessions)
async def get_session(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Retrieve an existing session.
    """
    # Validate UUID format (API-002)
    validate_uuid(session_id)

    try:
        return await _session_service.get_session(db, session_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    tags=["analytics"],
)
@limiter.limit(get_rate_limit_analytics)
async def analytics_summary(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsSummary:
    """Get analytics summary (SEC-007: restricted to backend-only access).

    Requires X-Analytics-Key header. Endpoint disabled if key is not configured.
    """
    # Verify API key if configured (SEC-007)
    verify_analytics_api_key(request)

    return await _session_service.analytics_summary(db)
