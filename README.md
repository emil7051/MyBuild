# TCO Web Platform

A modern web platform for comparing the Total Cost of Ownership (TCO) of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. Built for truck operators, fleet managers, and the Transport Workers Union (TWU) to make informed decisions about fleet electrification.

## Overview

The TCO Web Platform helps truck operators get five-minute TCO insights through:

- **Interactive Wizard** - Three-step process to input vehicle selection, operating profile, and cost assumptions
- **Detailed Analysis** - 14 cost components including purchase, financing, fuel, maintenance, battery replacement, and residual value
- **Scenario Modeling** - Compare baseline, technology breakthrough, and oil crisis scenarios
- **Visual Insights** - Cost-per-km charts, payback timelines, and cost breakdowns
- **Session Persistence** - Save and review calculation sessions
- **Analytics Dashboard** - Aggregated insights for policy and advocacy work

### Key Features

- 16 pre-configured vehicles (8 BEV, 8 diesel) across light, medium, and articulated truck classes
- Shared TypeScript calculation engine with ±1% parity validation against committed fixtures
- Offline-capable progressive web app
- PostgreSQL session persistence with Redis caching
- RESTful API for integrations and analytics

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ and Bun 1.0+
- PostgreSQL 15+ (or use included Docker setup)
- Redis 7+ (or use included Docker setup)

### Local Development with Docker

The fastest way to get started:

```bash
# Start all services (frontend, backend, database, cache)
docker compose up --build

# Access the application
# Frontend: http://localhost:5000
# Backend API: http://localhost:8000/api/v1/health
```

### Manual Setup

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your database and Redis URLs

# Run database migrations
python -m backend.app.db.session

# Start the backend server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install

# Set up environment (if needed)
cp .env.example .env

# Start development server
bun run dev
```

#### Generate Shared Data Layer

The TypeScript calculator consumes generated data from the Python sources:

```bash
# Generate vehicle catalog and constants
python scripts/generate_vehicle_catalog_ts.py
```

## Project Structure

```
.
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API routes and endpoints
│   │   ├── core/         # Configuration and cache
│   │   ├── db/           # Database models and session
│   │   ├── models/       # Pydantic request/response schemas
│   │   └── services/     # Business logic layer
│   └── requirements.txt
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # UI components (wizard, results, shared)
│   │   ├── hooks/        # React hooks
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API clients
│   │   └── state/        # Zustand store
│   └── package.json
├── shared/               # Shared TypeScript code
│   ├── calculator/       # Shared TCO engine
│   ├── data/             # Generated from Python (vehicles, constants, scenarios)
│   └── types/            # TypeScript type definitions
├── data/                 # Authoritative data layer
│   ├── constants.py      # Global constants
│   ├── policies.py       # Policy definitions (rebates, carbon pricing)
│   ├── scenarios.py      # Economic scenarios
│   └── vehicles.py       # Vehicle specifications
├── scripts/              # Code generation and utilities
├── tests/                # Backend test suite
├── archive/              # Historical documentation and legacy Python engine
└── docker-compose.yml    # Local development orchestration
```

## Key Technologies

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Hook Form + Zod** - Form validation
- **Recharts** - Data visualization
- **Vitest** - Testing

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database
- **Redis** - Session caching
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Calculation Engine
- **TypeScript** - Shared calculator logic under `shared/calculator`
- **Vitest** - Calculator regression tests against committed verification fixtures

## Stability & Robustness

The calculator engine and frontend include multiple layers of defensive programming:

### Input Validation
- **Runtime sanitization** - All calculation inputs are sanitized at the calculator entry point to prevent NaN propagation
- **Zod schemas** - Form inputs validated with comprehensive Zod schemas including vehicle parameter overrides
- **Duty cycle validation** - Real-time sum validation (must equal 100%) with visual feedback
- **Store validation** - Runtime validation in Zustand store prevents invalid state

### State Management
- **Race condition prevention** - Session creation uses mutex pattern to prevent duplicate sessions
- **Stale closure protection** - Generation counter pattern prevents outdated calculation results from overwriting newer ones
- **Cache versioning** - Vehicle catalog includes version tracking to invalidate stale localStorage cache on updates
- **Autosave feedback** - Toast notifications inform users when autosave fails

### Test Coverage
The test suite includes:
- **Calculator parity tests** - Validates TypeScript results match Python reference implementation (±1 cent tolerance)
- **Math utility tests** - Unit tests for NPV, annuity, and discounting functions
- **Scenario tests** - All three economic scenarios (baseline, technology_breakthrough, oil_crisis)
- **Edge case tests** - Zero values, NaN handling, boundary conditions, all 16 vehicles
- **Override tests** - Vehicle parameter and cost override combinations
- **State management tests** - Zustand store validation and race condition handling

Run all tests:
```bash
cd frontend && bun test
```

## Development Workflow

### Running Tests

```bash
# Backend tests
pytest tests/ --cov

# Frontend tests (all)
cd frontend
bun test

# Calculator parity tests only
cd frontend
bun test verification.test.ts

# Run with coverage
cd frontend
bun test --coverage
```

### Code Quality

```bash
# Python linting and formatting
ruff check .
black .
isort .
mypy .

# TypeScript linting and type checking
cd frontend
bun run lint
bun run typecheck
```

### Data Generation

Whenever you modify data in `data/` (vehicles, scenarios, policies, constants):

```bash
# Regenerate TypeScript types and data
python scripts/generate_vehicle_catalog_ts.py

# Run parity tests to ensure consistency
cd frontend
bun test
```

## API Documentation

See [API.md](./API.md) for complete API documentation including:
- Available endpoints
- Request/response schemas
- Authentication (if applicable)
- Usage examples

## Documentation

- **README.md** (this file) - Quick start and overview
- **[API.md](./API.md)** - REST API documentation
- **[AGENTS.md](./AGENTS.md)** - Development guidelines and conventions
- **[replit.md](./replit.md)** - Detailed architecture and design patterns

### Historical Documentation

The `archive/` folder contains:
- **archive/Transition Docs/** - Development transformation logs and execution plans
- **archive/legacy/** - Original Python CLI implementation

## Contributing

1. Follow the coding style guidelines in [AGENTS.md](./AGENTS.md)
2. Run tests and linters before committing
3. Update documentation for any API or data model changes
4. Regenerate shared TypeScript files when modifying Python data layer

## License

Copyright Transport Workers Union. All rights reserved.

## Support

For issues, questions, or contributions, contact the development team or open an issue.
