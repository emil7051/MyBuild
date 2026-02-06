# TCO Web Platform Architecture Notes

This document captures the current architecture and operating decisions for the live codebase.

## Current Decisions (Verified 2026-02-06)

- TypeScript calculator (`shared/calculator`) is the source of truth for TCO math.
- Deployment target is Replit autoscale with a Replit-managed PostgreSQL database.
- Docker hardening/compose findings from historical audits are de-scoped for this repo state.
- Session authorization is cookie-based for read/update (`HttpOnly` secret cookie, SHA-256 hash at rest).
- Backend observability baseline is implemented, including structured request logs, request IDs, sampled tracing, and alert events.
- Cost breakdown output uses grouped structures: `npv_costs`, `nominal_costs`, `upfront_costs`.

## System Overview

The platform helps operators compare BEV vs diesel truck ownership over a 15-year horizon.

Core capabilities:
- Guided 3-step frontend wizard.
- Scenario modeling (`baseline`, `technology_breakthrough`, `oil_crisis`).
- Comparison visualizations (cost per km, grouped cost breakdown, payback timeline, savings analysis).
- Session persistence and analytics summaries.

## Monorepo Layout

- `frontend/`: React + TypeScript web app.
- `backend/`: FastAPI service for vehicles, sessions, analytics, and static app serving.
- `shared/`: Shared calculator, shared types, generated data catalogs.
- `data/`: Python source-of-truth constants/scenarios/vehicles/policies.
- `scripts/`: data generation and validation tooling.
- `tests/`: backend tests.

## Data and Calculation Flow

1. Python data files in `data/` define authoritative constants/scenarios/vehicles/policies.
2. `scripts/generate_vehicle_catalog_ts.py` generates `shared/data/*.ts` artifacts.
3. Frontend builds calculation payloads and runs calculations via `shared/calculator`.
4. Backend persists wizard state/results and exposes analytics rollups.

Notes:
- Session payloads are validated server-side with Pydantic and shared override bounds.
- Scenario identifiers are normalized to canonical keys for storage/analytics consistency.

## Frontend Architecture

Stack:
- React 18, TypeScript (strict), Vite.
- Zustand for app state.
- React Hook Form + Zod for validation.
- TanStack Query for async mutation flow.
- Recharts for charts.
- Vitest + Playwright for tests.

Patterns:
- Wizard state persisted in local storage with catalog-version invalidation.
- `buildComparisonPayload` centralizes request construction and duty-cycle validation.
- Results routes/charts use lazy loading (`React.lazy` + `Suspense`).

## Backend Architecture

Stack:
- FastAPI, SQLAlchemy (async), Alembic.
- PostgreSQL persistence.
- Redis session cache (with graceful fallback).
- Slowapi rate limiting.

Endpoints:
- `/api/v1/vehicles`
- `/api/v1/sessions`
- `/api/v1/analytics/summary`

Security and traffic controls:
- UUID validation on session routes.
- Cookie-based session authorization for `GET/PUT /sessions/{session_id}`.
- Request body size limits (content-length and streaming checks).
- Rate limits for vehicles, sessions, and analytics.

## Observability Baseline

Implemented in middleware/config:
- Structured JSON request logs.
- `x-request-id` propagation.
- Sampled tracing with optional OTLP export and `x-trace-id` header on sampled requests.
- In-memory route-grouped metrics.
- Threshold-based alert events (`event=http.alert`) with optional webhook dispatch.

Operational guide:
- `docs/replit-deployment-runbook.md`

## CI and Quality Gates

Primary workflows:
- `.github/workflows/ci.yml`
- `.github/workflows/dependency-audit.yml`
- `.github/workflows/data-sync-check.yml`

CI includes:
- Backend lint/test/typecheck jobs.
- Frontend lint/typecheck/test/e2e/build jobs.
- Lockfile/frozen install usage for reproducibility (`bun install --frozen-lockfile`).

## Dependencies

Runtime dependencies:
- `requirements.txt` + `requirements.lock.txt`

Dev/test dependencies:
- `requirements-dev.txt` + `requirements-dev.lock.txt`

Optional analysis/script dependencies:
- `requirements-scripts.txt`

## Testing Notes

Backend:
- `python -m pytest tests --cov`

Frontend:
- `cd frontend && bun run test`
- `cd frontend && bun run test:e2e`

Data parity and integrity:
- `python scripts/validation.py`
- Shared verification fixtures in `shared/calculator/verification_data.json`
