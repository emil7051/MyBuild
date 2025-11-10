# Overview

The MyBuild TCO (Total Cost of Ownership) Calculator is a web platform that helps truck operators and fleet managers compare the economics of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. The application performs detailed financial modeling across 14 cost components including purchase costs, operating expenses, financing, maintenance, battery replacement, and residual value calculations. It supports scenario analysis (baseline, technology breakthrough, oil crisis) and provides both individual calculations and fleet-wide comparisons across light rigid, medium rigid, and articulated truck classes.

The platform consists of three main parts:
1. A proven Python calculation engine (legacy codebase) that implements the TCO math
2. A modern React + TypeScript frontend wizard that guides users through vehicle selection, operating profiles, and cost overrides
3. A FastAPI backend that wraps the Python engine, provides REST endpoints, and manages session persistence via PostgreSQL and Redis

The shared TypeScript calculator mirrors the Python engine to enable client-side calculations with API fallback, ensuring accuracy parity within ±1% across all scenarios.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Pattern

**Monorepo Structure with Shared Data Layer**: The repository uses a monorepo layout where frontend, backend, and shared modules coexist. Python scripts (`scripts/generate_vehicle_catalog_ts.py`) generate TypeScript data files (`shared/data/*.ts`) from authoritative Python sources (`data/*.py`), ensuring the frontend and backend share identical vehicle specifications, constants, scenarios, and policy definitions.

**Dual Calculator Pattern**: The system maintains two calculation engines that must stay in parity:
- **Python Engine** (`calculations/`): The source of truth, used by backend API and legacy CLI tools
- **TypeScript Engine** (`shared/calculator/`): Client-side mirror for instant feedback, falls back to API when needed

Both engines implement the same 15-year discounted cash flow model with 14 cost components. A parity harness (`scripts/export_tco_snapshot.py`) validates that TypeScript results match Python within ±1%.

## Data Flow Architecture

**Three-Tier Calculation Flow**:
1. **Input Layer** (`calculations/inputs.py`, `VehicleInputs` dataclass): Pre-calculates all subcomponents (stamp duty, rebates, financing terms, depreciation schedules) from vehicle specs, scenario parameters, and purchase method
2. **Calculator Layer** (`calculations/financial.py`, `calculations/operating.py`): Applies year-by-year trajectories for fuel/electricity prices, efficiency curves, battery degradation, and maintenance costs
3. **Aggregation Layer** (`calculations/calculations.py`, `TCOResult`): Discounts all future costs to present value, calculates total cost, annual cost, and cost-per-km metrics

**Wizard State Management**: The frontend uses Zustand for global state (vehicle selections, scenario choice, overrides) with React Hook Form + Zod for validation. The wizard persists selections to backend sessions via `/sessions` endpoints, enabling resume/export workflows.

## Frontend Architecture

**Progressive Wizard Pattern**: Three-step wizard (vehicle selection → operating profile → cost overrides) with field-level validation, smart defaults, and inline help text. Built with React 18, Vite, Tailwind CSS, and React Router.

**Optimistic Calculation Strategy**: The wizard runs calculations client-side using the shared TypeScript calculator when possible, falling back to FastAPI endpoints when overrides require server-side policy logic. Results are cached in Zustand and persisted to the backend via session APIs.

**Component Structure**:
- `pages/WizardPage.tsx`: Orchestrates the multi-step form
- `components/wizard/*`: Step-specific components (vehicle selection, operating profile, cost inputs)
- `components/results/*`: Results dashboard with cost breakdowns and Recharts visualizations
- `state/tcoStore.ts`: Zustand store managing wizard data, cached results, and calculation state

## Backend Architecture

**FastAPI Service Layer**: The backend (`backend/app/`) wraps the legacy Python engine in REST endpoints:
- `/api/v1/calculations`: Single-vehicle TCO calculation
- `/api/v1/calculations/compare`: Multi-vehicle comparison
- `/api/v1/vehicles`: Vehicle catalog endpoints
- `/api/v1/sessions`: Session CRUD for persistence and resume
- `/api/v1/analytics/summary`: Aggregated telemetry dashboard

**Service Pattern**: Domain logic lives in service classes (`services/calculations.py`, `services/sessions.py`) that translate HTTP requests into Python engine calls and marshal responses into Pydantic schemas.

**Caching Strategy**: In-memory result caching (toggled via `CACHE_RESULTS` env var) and Redis session snapshots (30-minute TTL) reduce duplicate calculations and enable fast wizard resume.

## Database Schema

**SQLAlchemy Async Models** (`backend/app/db/models.py`):
- `SessionRecord`: Stores wizard state, cached results, timestamps
- `UserInputRecord`: Normalized vehicle selections and overrides per session
- `CalculationResultRecord`: Full TCO breakdown snapshots
- `OperatorProfileRecord`: Optional operator metadata (fleet size, routes, opt-in)
- `FeedbackRecord`: User feedback and scenario satisfaction ratings

Postgres is used in production; SQLite via `aiosqlite` for local dev. Redis (`redis://localhost:6379/0`) caches session snapshots.

## Calculation Engine Design

**Modular Calculator Architecture** (`calculations/`):
- `financial.py`: Stamp duty, rebates, financing (PMT formula via numpy-financial), depreciation schedules
- `operating.py`: Fuel/electricity costs with efficiency trajectories, maintenance curves, battery replacement logic (year-based triggers), insurance, payload penalties, carbon pricing
- `utils.py`: Financial primitives (NPV, PV, discounting helpers)
- `simulation.py`: Monte Carlo and sensitivity analysis (uncertainty parameters, percentile outputs)

**Scenario System** (`data/scenarios.py`): `EconomicScenario` dataclasses define time-varying parameters (diesel/electricity price trajectories, battery cost decline, efficiency improvements). Three predefined scenarios (baseline, technology breakthrough, oil crisis) plus custom scenario builder.

**Policy Toggles** (`data/policies.py`): Dataclass-based policy definitions (purchase rebates, stamp duty exemptions, carbon pricing, green loan subsidies, charging infrastructure grants) with enable/disable switches and parameter tuning.

## Code Generation Pipeline

**Shared Data SDK**: `scripts/generate_vehicle_catalog_ts.py` reads Python dataclasses and emits TypeScript files:
- `shared/data/vehicleCatalog.ts`: All 16 vehicle models with full specs
- `shared/data/constants.ts`: Global constants (discount rate, battery costs, charging mix)
- `shared/data/scenarios.ts`: Scenario definitions with trajectories
- `shared/data/policies.ts`: Policy configuration catalog

This ensures frontend and backend consume identical datasets without manual synchronization.

**Parity Validation**: `scripts/export_tco_snapshot.py` generates JSON snapshots of Python engine results (all vehicles × scenarios × purchase methods × override stress tests). Frontend Vitest tests import these snapshots and verify TypeScript calculator outputs match within ±1%.

# External Dependencies

## Third-Party Services

**None in current implementation** - The application runs entirely self-hosted. Future roadmap may include:
- Sentry for error monitoring (mentioned in master plan)
- Analytics/telemetry platform for operator data insights
- Export integrations (CSV/HTML report generation currently uses local file system)

## Databases

**PostgreSQL** (via SQLAlchemy + asyncpg):
- Connection string: `postgresql+asyncpg://user:pass@localhost:5432/tco_db`
- Used for session persistence, calculation history, operator profiles, feedback
- Async engine with connection pooling

**Redis**:
- Connection string: `redis://localhost:6379/0`
- TTL-based session caching (default 30 minutes)
- Used to speed up wizard resume and reduce database reads

**SQLite** (development fallback):
- Connection string: `sqlite+aiosqlite:///./tco.db`
- Used when `DATABASE_URL` not set, suitable for local dev and testing

## Key Python Libraries

**Core Calculation**:
- `numpy` / `numpy-financial`: Financial functions (PMT, NPV calculations)
- `pandas`: Data manipulation for exports and analysis
- `plotly`: Chart generation (legacy output system)

**Backend Framework**:
- `fastapi`: Async web framework
- `uvicorn`: ASGI server
- `pydantic` / `pydantic-settings`: Schema validation, environment config
- `sqlalchemy`: Async ORM with PostgreSQL/SQLite support
- `redis[asyncio]`: Async Redis client

**Testing & Quality**:
- `pytest` + `pytest-cov` + `pytest-mock` + `pytest-xdist`: Test framework
- `black` + `isort` + `ruff`: Code formatting and linting
- `mypy`: Static type checking

## Key Frontend Libraries

**Framework & Build**:
- `react` 18.2 + `react-dom`: UI framework
- `vite`: Build tool and dev server
- `typescript`: Type safety

**State & Data**:
- `zustand`: Global state management (wizard data, results cache)
- `@tanstack/react-query`: Server state management, API calls
- `axios`: HTTP client
- `zod`: Schema validation
- `react-hook-form` + `@hookform/resolvers`: Form state and validation

**UI & Visualization**:
- `tailwindcss`: Utility-first CSS framework
- `recharts`: Chart library for cost breakdowns
- `react-router-dom`: Client-side routing
- `react-hot-toast`: Toast notifications

**Testing**:
- `vitest`: Unit test runner (TypeScript parity tests)
- `@vitejs/plugin-react`: React support in Vitest

## Development Tools

**Pre-commit Hooks**: `.pre-commit-config.yaml` enforces `black`, `isort`, `ruff`, `mypy` on Python files before commits.

**Docker Compose**: `docker-compose.yml` orchestrates frontend, backend, Postgres, and Redis services with shared networking and environment files.

**CI/CD**: GitHub Actions (`.github/workflows/ci.yml`) runs lint/type/test gates on Node 20 + Python 3.11 for every PR.

## Environment Configuration

**Backend** (`.env` file, loaded via `pydantic-settings`):
- `DATABASE_URL`: SQLAlchemy connection string
- `REDIS_URL`: Redis connection string
- `BACKEND_CORS_ORIGINS`: Comma-separated allowed origins
- `CACHE_RESULTS`: Boolean toggle for in-memory caching
- `SESSION_TTL_SECONDS`: Redis session TTL (default 1800)

**Frontend** (Vite env vars):
- `VITE_API_URL`: Backend API base URL (default `http://localhost:8000/api/v1`)

All secrets managed via `.env.example` template; actual `.env` files are gitignored.