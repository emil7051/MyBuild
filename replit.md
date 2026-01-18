# Overview

The MyBuild TCO (Total Cost of Ownership) Calculator is a web platform designed to help truck operators and fleet managers compare the economics of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. It performs detailed financial modeling across 14 cost components, including purchase, operating expenses, financing, maintenance, battery replacement, and residual value. The platform supports scenario analysis (baseline, technology breakthrough, oil crisis) and provides individual calculations and fleet-wide comparisons across light rigid, medium rigid, and articulated truck classes.

The system comprises a shared TypeScript calculation engine, a modern React + TypeScript frontend wizard, and a FastAPI backend. The legacy Python engine now lives in `archive/` for historical reference; the TypeScript calculator is the active source of truth.

# Recent Changes

**Production Release: November 10, 2025**

The application has been successfully deployed to production with the following features:

- **Complete**: All four development phases (Step 1-4) have been implemented and tested
- **Features Delivered**:
  - Interactive three-step wizard for vehicle selection, operating profile, and cost inputs
  - Real-time TCO calculations with the shared TypeScript engine (±1% parity validated)
  - Session persistence with PostgreSQL and Redis caching
  - Analytics dashboard with aggregated insights
  - Results visualization with cost breakdowns, comparison highlights, and charts
- **Code Cleanup**: Legacy code and transition documentation moved to `archive/` folder
- **Documentation**: Comprehensive documentation added (README.md, API.md)
- **Production-Ready**: Database schema finalized, caching optimized, error handling implemented

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Patterns

**Monorepo Structure with Shared Data Layer**: The project uses a monorepo containing frontend, backend, and shared modules. Python scripts generate TypeScript data files from authoritative Python sources, ensuring identical vehicle specifications, constants, scenarios, and policy definitions are shared between frontend and backend.

**Shared Calculator Pattern**: The system uses a single TypeScript calculator (shared across frontend and backend contexts) that implements a 15-year discounted cash flow model with 14 cost components, validated for ±1% parity against committed fixtures. The legacy Python engine is archived and no longer called at runtime.

## Data Flow Architecture

**Three-Tier Calculation Flow**: Calculations proceed through an Input Layer (pre-calculates subcomponents), a Calculator Layer (applies year-by-year trajectories), and an Aggregation Layer (discounts future costs to present value and calculates metrics).

**Wizard State Management**: The frontend uses Zustand for global state and React Hook Form + Zod for validation. Selections are persisted to backend sessions via `/sessions` endpoints.

## Frontend Architecture

**Progressive Wizard Pattern**: A three-step wizard (vehicle selection → operating profile → cost overrides) with validation, smart defaults, and inline help. Built with React 18, Vite, Tailwind CSS, and React Router.

**Optimistic Calculation Strategy**: Calculations run in the shared TypeScript calculator on the client; the backend handles policy data exposure, session persistence, and analytics. Results are cached locally and persisted to the backend.

## Backend Architecture

**FastAPI Service Layer**: The backend exposes REST endpoints for vehicle catalog access, session management, and analytics; calculation endpoints now rely on the shared TypeScript engine rather than the archived Python implementation.

**Service Pattern**: Domain logic is organized into service classes that translate HTTP requests to calculator calls and marshal responses using Pydantic schemas.

**Caching Strategy**: In-memory result caching and Redis session snapshots (30-minute TTL) are used to improve performance.

## Database Schema

SQLAlchemy Async Models define the database schema, including `SessionRecord`, `UserInputRecord`, `CalculationResultRecord`, `OperatorProfileRecord`, and `FeedbackRecord`. PostgreSQL is used in production, with SQLite for local development. Redis caches session snapshots.

## Calculation Engine Design

**Modular Calculator Architecture**: The `shared/calculator/` directory contains modules for financial modeling, operating costs, utilities, and simulation (mirroring the archived Python layout in `archive/calculations_legacy/`).

**Scenario System**: `EconomicScenario` dataclasses define time-varying parameters (e.g., fuel prices, battery costs) across predefined and custom scenarios.

**Policy Toggles**: Dataclass-based policy definitions (e.g., rebates, carbon pricing) can be enabled/disabled and tuned.

## Code Generation Pipeline

**Shared Data SDK**: A Python script generates TypeScript files (`vehicleCatalog.ts`, `constants.ts`, `scenarios.ts`, `policies.ts`) from Python dataclasses, ensuring data consistency between frontend and backend.

**Parity Validation**: Vitest uses committed fixtures in `shared/calculator/verification_data.json` to keep the TypeScript calculator stable; the old Python snapshot generator has been retired.

# External Dependencies

## Databases

**PostgreSQL**: Used for session persistence, calculation history, operator profiles, and feedback. Configured with `postgresql+asyncpg` driver.

**Redis**: Used for TTL-based session caching (30 minutes TTL).

**SQLite**: Used for local development and testing.

## Key Python Libraries

**Core Calculation (legacy)**: `numpy`, `numpy-financial`, `pandas`, `plotly`.
**Backend Framework**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `redis[asyncio]`.
**Testing & Quality**: `pytest` and related plugins, `black`, `isort`, `ruff`, `mypy`.

## Key Frontend Libraries

**Framework & Build**: `react`, `react-dom`, `vite`, `typescript`.
**State & Data**: `zustand`, `@tanstack/react-query`, `axios`, `zod`, `react-hook-form`.
**UI & Visualization**: `tailwindcss`, `recharts`, `react-router-dom`, `react-hot-toast`.
**Testing**: `vitest`, `@vitejs/plugin-react`.

## Development Tools

**Pre-commit Hooks**: Enforce code quality standards.
**Docker Compose**: Orchestrates frontend, backend, Postgres, and Redis.
**CI/CD**: GitHub Actions for linting, type checking, and testing.
