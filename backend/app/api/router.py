"""Versioned API router that wires endpoints to services."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.db.session import get_db_session
from backend.app.models import (
    CalculationRequest,
    CalculationResponse,
    ComparisonRequest,
    VehicleDetail,
    VehicleSummary,
)
from backend.app.models.session import (
    AnalyticsSummary,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)
from backend.app.services import CalculationService, VehicleCatalogService
from backend.app.services.sessions import SessionService

api_router = APIRouter(prefix=settings.api_v1_prefix)

_calculation_service = CalculationService()
_vehicle_service = VehicleCatalogService()
_session_service = SessionService()


@api_router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@api_router.get("/vehicles", response_model=List[VehicleSummary], tags=["vehicles"])
def list_vehicles() -> List[VehicleSummary]:
    return _vehicle_service.list_summaries()


@api_router.get(
    "/vehicles/{vehicle_id}", response_model=VehicleDetail, tags=["vehicles"]
)
def get_vehicle(vehicle_id: str) -> VehicleDetail:
    try:
        return _vehicle_service.get(vehicle_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.post(
    "/calculations", response_model=CalculationResponse, tags=["calculations"]
)
def run_calculation(request: CalculationRequest) -> CalculationResponse:
    try:
        return _calculation_service.calculate(request)
    except (KeyError, ValueError) as exc:  # pragma: no cover
        status_code = 404 if isinstance(exc, KeyError) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@api_router.post(
    "/calculations/compare",
    response_model=List[CalculationResponse],
    tags=["calculations"],
)
def compare_calculations(request: ComparisonRequest) -> List[CalculationResponse]:
    try:
        return list(_calculation_service.compare(request))
    except (KeyError, ValueError) as exc:  # pragma: no cover
        status_code = 404 if isinstance(exc, KeyError) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@api_router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["sessions"],
)
async def create_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    try:
        return await _session_service.create_session(db, payload)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.put(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    try:
        return await _session_service.update_session(db, session_id, payload)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
async def get_session(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    try:
        return await _session_service.get_session(db, session_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    tags=["analytics"],
)
async def analytics_summary(
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsSummary:
    return await _session_service.analytics_summary(db)
