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
- Client-side and server-side calculation engines with ±1% parity validation
- Offline-capable progressive web app
- PostgreSQL session persistence with Redis caching
- RESTful API for integrations and analytics

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
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
pip install -r requirements.txt

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
npm install

# Set up environment (if needed)
cp .env.example .env

# Start development server
npm run dev
```

#### Generate Shared Data Layer

The TypeScript frontend uses data generated from the Python source:

```bash
# Generate vehicle catalog and constants
python scripts/generate_vehicle_catalog_ts.py

# Generate TCO calculation snapshots for testing
python scripts/export_tco_snapshot.py
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
│   ├── calculator/       # Client-side TCO engine
│   ├── data/             # Generated from Python (vehicles, constants, scenarios)
│   └── types/            # TypeScript type definitions
├── calculations/         # Python TCO calculation engine
│   ├── financial.py      # Purchase, financing, depreciation
│   ├── operating.py      # Fuel, maintenance, insurance costs
│   ├── simulation.py     # Monte Carlo and sensitivity analysis
│   └── calculations.py   # Core TCO aggregation
├── data/                 # Authoritative data layer
│   ├── constants.py      # Global constants
│   ├── policies.py       # Policy definitions (rebates, carbon pricing)
│   ├── scenarios.py      # Economic scenarios
│   └── vehicles.py       # Vehicle specifications
├── scripts/              # Code generation and utilities
├── tests/                # Python test suite
├── archive/              # Historical documentation and legacy code
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
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation
- **NumPy Financial** - Financial calculations

## Development Workflow

### Running Tests

```bash
# Backend tests
pytest tests/ --cov

# Frontend tests
cd frontend
npm run test

# Parity tests (validates TypeScript matches Python)
cd frontend
npm run test -- TCOEngine.test.ts
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
npm run lint
npm run typecheck
```

### Data Generation

Whenever you modify data in `data/` (vehicles, scenarios, policies, constants):

```bash
# Regenerate TypeScript types and data
python scripts/generate_vehicle_catalog_ts.py
python scripts/export_tco_snapshot.py

# Run parity tests to ensure consistency
cd frontend
npm run test
```

## API Documentation

See [API.md](./API.md) for complete API documentation including:
- Available endpoints
- Request/response schemas
- Authentication (if applicable)
- Usage examples

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment instructions.

## Troubleshooting

Having issues? Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions to common problems including:
- Docker and environment setup
- Frontend build and runtime errors
- Backend API and database connection issues
- Deployment and production problems

## Documentation

- **README.md** (this file) - Quick start and overview
- **[API.md](./API.md)** - REST API documentation
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and fixes
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
