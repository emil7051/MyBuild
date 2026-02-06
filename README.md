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
- Shared TypeScript calculation engine validated against Python reference implementation
- Offline-capable progressive web app
- PostgreSQL session persistence with Redis caching
- RESTful API for integrations and analytics

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ and Bun 1.0+
- PostgreSQL 15+
- Redis 7+

### Manual Setup

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements-dev.lock.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your database and Redis URLs

# Run database migrations (creates schema if new, applies pending migrations otherwise)
cd backend && alembic upgrade head

# Start the backend server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Ensure PostgreSQL and Redis are running before starting the backend.

#### Observability Production Defaults (OBS-02)

For production (including Replit deployments), start with these backend environment values:

```bash
OBSERVABILITY_TRACING_ENABLED=true
OBSERVABILITY_TRACING_SAMPLE_RATE=0.05
OBSERVABILITY_TRACING_SERVICE_NAME=tco-web-platform-api
# Optional: set to OTLP collector endpoint; leave unset to emit sampled spans to stdout logs
OBSERVABILITY_TRACING_OTLP_ENDPOINT=
OBSERVABILITY_TRACING_OTLP_HEADERS=

OBSERVABILITY_ALERT_MIN_REQUESTS=20
OBSERVABILITY_ALERT_ERROR_RATE_THRESHOLD=0.2
OBSERVABILITY_ALERT_AVG_DURATION_MS_THRESHOLD=1500
OBSERVABILITY_ALERT_COOLDOWN_SECONDS=300
# Optional: set to Slack/Teams/Pager bridge webhook
OBSERVABILITY_ALERT_WEBHOOK_URL=
OBSERVABILITY_ALERT_WEBHOOK_TIMEOUT_SECONDS=2.0
```

Operational behavior:
- API responses include `x-request-id`; sampled traced requests also include `x-trace-id`.
- Alerts are emitted as structured log events with `event=http.alert`; optional webhook forwarding is supported.
- Start with the defaults above and tune thresholds after observing live traffic patterns.

See `docs/replit-deployment-runbook.md` for full deployment and alerting workflow details.

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install --frozen-lockfile

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

#### Regenerate Python Lockfiles

When you change `requirements.txt` or `requirements-dev.txt`, regenerate lockfiles:

```bash
uv pip compile requirements.txt --output-file requirements.lock.txt --python-version 3.11 --universal
uv pip compile requirements.txt requirements-dev.txt --output-file requirements-dev.lock.txt --python-version 3.11 --universal --no-emit-package pip
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
└── archive/              # Historical documentation and legacy Python engine
```

## Key Technologies

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Query** - Server state management
- **React Hook Form + Zod** - Form validation
- **Recharts** - Data visualization
- **react-hot-toast** - Notifications
- **Vitest** - Unit testing
- **Playwright** - E2E testing

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database
- **Redis** - Session caching
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Calculation Engine
- **TypeScript** - Shared calculator logic under `shared/calculator`
- **Vitest** - Calculator parity tests (within 5 cents per component) against Python-generated fixtures

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
- **Calculator parity tests** - Validates TypeScript results match Python reference implementation (within 5 cents for dollar amounts, 0.05 cents for cost_per_km)
- **Math utility tests** - Unit tests for NPV, annuity, and discounting functions
- **Scenario tests** - All three economic scenarios (baseline, technology_breakthrough, oil_crisis)
- **Edge case tests** - Zero values, NaN handling, boundary conditions, all 16 vehicles
- **Override tests** - Vehicle parameter and cost override combinations
- **State management tests** - Zustand store validation and race condition handling

Run all tests:
```bash
# Unit tests
cd frontend && bun run test

# E2E tests (requires dev server running)
cd frontend && bun run test:e2e
```

## Database Migrations

The backend uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Migrations are applied automatically on app startup, but can also be run manually.

### Running Migrations

```bash
# Navigate to backend directory
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history
```

### Creating New Migrations

When modifying database models:

```bash
cd backend

# Generate a new migration (auto-detects model changes)
alembic revision --autogenerate -m "Description of changes"

# Or create an empty migration for manual edits
alembic revision -m "Description of changes"
```

### Migration Best Practices

- **Always review auto-generated migrations** before applying them
- **Test migrations on a copy of production data** before deploying
- **Keep migrations small and focused** on one logical change
- **Never modify a migration that has been applied** in production
- Migrations support both SQLite (development) and PostgreSQL (production)

### Rolling Back

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations (use with caution!)
alembic downgrade base
```

## Security

The project includes automated security scanning and follows best practices for secure development. See [SECURITY.md](./SECURITY.md) for:

- Vulnerability scanning policy and fail thresholds
- Dependency audit procedures (Python and frontend)
- Security reporting process
- Backend and frontend security features

### Dependency Vulnerability Scanning

Dependencies are automatically audited in CI on every push and PR:

```bash
# Run Python dependency audit locally
pip-audit -r requirements.lock.txt

# Run frontend dependency audit locally
cd frontend && bun audit
```

The CI workflow runs weekly scheduled scans to detect newly disclosed vulnerabilities.

## Development Workflow

### Running Tests

```bash
# Backend tests
pytest tests/ --cov

# Frontend unit tests (all)
cd frontend
bun run test

# Calculator verification tests only
cd frontend
bun run test -- verification.test.ts

# Run with coverage
cd frontend
bunx vitest run --coverage

# E2E tests (requires dev server running on localhost:5000)
cd frontend
bun run test:e2e

# E2E tests with UI mode (for debugging)
cd frontend
bunx playwright test --ui
```

### Code Quality

```bash
# Python linting and formatting
ruff check .
black .
isort .
mypy backend/app/core backend/app/api backend/app/main.py

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

# Run verification tests to ensure consistency
cd frontend
bun run test
```

## API Documentation

See [API.md](./API.md) for complete API documentation including:
- Available endpoints
- Request/response schemas
- Session authorization and analytics API key requirements
- Usage examples

## Documentation

- **README.md** (this file) - Quick start and overview
- **[API.md](./API.md)** - REST API documentation
- **[AGENTS.md](./AGENTS.md)** - Development guidelines and conventions
- **[SECURITY.md](./SECURITY.md)** - Security policy and vulnerability management
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
