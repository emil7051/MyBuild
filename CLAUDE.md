# TCO Web Platform - Claude Instructions

## Agent Model Requirements

**IMPORTANT**: Always use `opus` (Claude Opus 4.5) for all Task tool sub-agents. Never use `haiku` or `sonnet` for this project. The complexity of the codebase requires the highest capability model.

```
Task tool calls must include: model: "opus"
```

## Project Overview

A web platform for comparing Total Cost of Ownership (TCO) of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. Built for truck operators, fleet managers, and the Transport Workers Union (TWU).

**Key features:**
- Interactive 3-step wizard:
  1. Select your diesel truck
  2. Select electric trucks to compare
  3. Configure operating profile/cost assumptions and view results
- 14 cost components including purchase, financing, fuel, maintenance, battery replacement, residual value
- Scenario modeling (baseline, technology breakthrough, oil crisis)
- Visual insights with cost-per-km charts, payback timelines, cost breakdowns
- Session persistence and analytics dashboard

## Package Manager

Always use `bun` instead of `npm` or `yarn` for frontend operations.

## Technology Stack

### Frontend
- React 18 + TypeScript (strict mode)
- Vite build tool
- TailwindCSS for styling
- Zustand for state management
- React Query (@tanstack/react-query) for server state
- React Hook Form + Zod for validation
- Recharts for data visualization
- react-hot-toast for notifications
- Vitest for testing (Playwright for E2E)

### Backend
- FastAPI (Python)
- SQLAlchemy with async support
- PostgreSQL database
- Redis caching
- Pydantic validation

### Shared
- TypeScript calculator engine in `shared/calculator/`
- Generated types from Python in `shared/types/`

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, cache, security, middleware
│   │   ├── db/           # Models and session
│   │   ├── models/       # Pydantic schemas
│   │   └── services/     # Business logic
├── frontend/             # React + TypeScript
│   ├── src/
│   │   ├── components/   # UI components (wizard, results, shared, layout)
│   │   ├── hooks/        # React hooks
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API clients
│   │   ├── state/        # Zustand store
│   │   └── test/         # Vitest test files
│   └── e2e/              # Playwright E2E tests
├── shared/               # Shared TypeScript code
│   ├── calculator/       # TCO engine (source of truth)
│   │   └── verification_data.json  # Python-generated test fixtures
│   ├── data/             # Generated from Python + manual constants
│   │   ├── *.generated.ts  # Auto-generated (don't edit)
│   │   └── constants.future.ts  # Manually maintained
│   └── types/            # TypeScript type definitions
├── data/                 # Authoritative Python data layer
│   ├── constants.py
│   ├── policies.py
│   ├── scenarios.py
│   └── vehicles.py
├── scripts/              # Code generation and validation utilities
├── tests/                # Backend test suite
└── archive/              # Historical docs and legacy Python engine
```

## Key Commands

**Development:**
```bash
docker compose up --build          # Start all services
# Frontend: http://localhost:5000
# Backend API: http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend && bun install         # Install dependencies
bun run dev                        # Start dev server
bun run build                      # Production build
bun run lint                       # ESLint
bun run typecheck                  # TypeScript check
bun test                           # Run tests
```

**Backend:**
```bash
pip install -r requirements.txt -r requirements-dev.txt
uvicorn backend.app.main:app --reload
pytest tests/ --cov                # Run tests with coverage
```

**Data Generation (run when modifying data/*.py):**
```bash
python scripts/generate_vehicle_catalog_ts.py
# Generates 4 files in shared/data/:
# - vehicleCatalog.ts (vehicle specs)
# - constants.generated.ts (calculation constants)
# - scenarios.ts (economic scenarios)
# - policies.ts (rebates, carbon pricing)
```

## Code Style

**Python:**
- 4-space indents, type hints, Google-style docstrings
- Format/lint with: `ruff check .`, `black .`, `isort .`

**TypeScript:**
- 2-space indent, single quotes, strict mode
- Components: PascalCase
- Hooks: useCamelCase
- Import DTOs from `shared/types`

## Testing Requirements

- Calculator parity tests validate TypeScript matches Python reference (within 5 cents for dollar amounts, 0.05 cents for cost_per_km)
- Run `bun test` before committing frontend changes
- Run `pytest tests/` before committing backend changes

## Chart Conventions (Important)

The `CostBreakdown` type has **mixed value bases** - see `shared/types/tco.types.ts`:

**NPV-adjusted fields:** fuel_cost, maintenance_cost, battery_replacement_cost, carbon_cost, charging_labour_cost, payload_penalty_cost, residual_value

**Nominal lifetime totals (NOT discounted):** insurance_cost, registration_cost, depreciation

**Upfront values:** purchase_cost, taxes_and_fees

**Note:** `financing_cost` is total loan interest over the term, NOT an upfront payment.

The `total_cost` in `CalculationResponsePayload` IS fully NPV-adjusted and represents the true economic comparison.

## Serena MCP Best Practices

This project uses Serena for semantic code navigation and editing.

### Use Symbolic Tools First
```
find_symbol(name_path="MyClass/myMethod", include_body=True)
```
Faster and uses less context than reading whole files.

### Leverage Substring Matching
```
find_symbol(name_path="handler", substring_matching=True)
```

### Use Regex Mode in `replace_content`
```
replace_content(needle="old_pattern.*?end", repl="new_content", mode="regex")
```
Use non-greedy `.*?` to avoid matching too much.

### Keep Memories Updated
After significant work, update memories with `write_memory`. Review `.serena/memories/` periodically.

### Think Tools
Use `think_about_collected_information` after research and `think_about_task_adherence` before making edits.

## Merge Gate Checklist

- [ ] Backend: `pytest tests/ --cov`
- [ ] Frontend: `cd frontend && bun test`
- [ ] Lint: `bun run lint && bun run typecheck`
- [ ] Data regen (if touching `data/*.py`): `python scripts/generate_vehicle_catalog_ts.py`
