# Repository Guidelines

## Documentation Structure

The project includes comprehensive documentation:

- **[README.md](./README.md)** - Quick start guide and project overview
- **[API.md](./API.md)** - Complete REST API documentation with examples
- **[replit.md](./replit.md)** - Detailed architecture and design patterns
- **[AGENTS.md](./AGENTS.md)** (this file) - Development guidelines and conventions

Historical documentation and legacy code are archived in the `archive/` folder:
- `archive/Transition Docs/` - Development transformation logs and execution plans
- `archive/legacy/` - Original Python CLI implementation and legacy analysis tools

## Project Structure & Module Organization

The project follows a monorepo structure: the TypeScript calculator in `shared/calculator` is the source-of-truth engine, backed by Python data under `data/` and regenerated TypeScript contracts in `shared/types`. `scripts/` carries `generate_vehicle_catalog_ts.py` and `validation.py`, and Docker assets keep the Postgres/Redis topology reproducible.

## Build, Test, and Development Commands

**Quick Start:**
- `docker compose up --build` - Start all services (recommended for development)
- Visit `http://localhost:5000` for frontend, `http://localhost:8000/docs` for API docs

**Python Setup:**
- `python -m pip install -r requirements.txt -r requirements-dev.txt && pre-commit install` primes Python tooling
- `python scripts/generate_vehicle_catalog_ts.py` refreshes the shared SDK before frontend or API work
- `uvicorn backend.app.main:app --reload` boots FastAPI standalone

**Frontend Setup:**
- `cd frontend && bun install && bun run dev` starts the wizard
- `bun run build|lint|typecheck` satisfy CI gates

**Testing:**
- `python -m pytest tests --cov` runs backend tests
- `cd frontend && bun run test` runs frontend tests and enforces the ±1% parity budget using the TypeScript calculator fixtures

See [README.md](./README.md) for complete development setup instructions.

## Coding Style & Naming Conventions

Python files use 4-space indents, type hints, and Google-style docstrings; run `ruff check .`, `black .`, and `isort .` pre-push. TypeScript remains in strict mode with ESLint/Prettier defaults (2-space indent, single quotes). Keep components `PascalCase`, hooks `useCamelCase`, and import DTOs from `shared/types` to keep every layer on the same contract.

## Testing & Parity Guidelines

Use `python scripts/validation.py` whenever vehicle, scenario, or policy data changes, and seed Monte Carlo helpers for reproducible CI. Keep the shared TypeScript calculator and Vitest suite within ±1% of the stored verification fixtures, and include parity evidence with each PR.

## Merge Gate Checklist

- [ ] Backend: `python -m pytest tests --cov`
- [ ] Frontend/unit: `cd frontend && bun run test`
- [ ] Data regen: if touching `data/*.py` or `scripts/*`, run `python scripts/generate_vehicle_catalog_ts.py` and ensure generated TS stays in sync

## Commit & Pull Request Guidelines

Commits stay concise and imperative ("Add web app backend, frontend, and shared packages"), stay under 72 characters, and tag subsystems (`backend:`, `frontend:`, `shared:`). PRs should describe scope, list executed commands (pytest, Vitest, lint, exports), flag schema or data migrations, attach artefacts when UX or CSV outputs change, and request reviewers from each affected discipline.

## Security & Configuration Tips

Use `.env.example` as the template for secrets; load variables via `python-dotenv`/`pydantic-settings` so FastAPI, scripts, and Docker read the same source. Never commit operator data or credentials inside `data/` or `frontend/public`. Run `pip-audit`, `bun audit`, and `bandit` whenever dependencies move, regenerate shared types when `data/*.py` changes. Historical data revisions are documented in `archive/Transition Docs/TRANSFORMATION_EXECUTION_LOG.md`.

## Serena MCP Best Practices

This project uses Serena for semantic code navigation and editing. Follow these practices for efficient workflows:

### Use Symbolic Tools First
Instead of reading entire files, use `find_symbol` with `include_body=True` for targeted reads:
```
find_symbol(name_path="MyClass/myMethod", include_body=True)
```
This is faster and uses less context than reading whole files.

### Leverage Substring Matching
When unsure of exact symbol names:
```
find_symbol(name_path="handler", substring_matching=True)
```

### Use Regex Mode in `replace_content`
For partial edits within symbols (when `replace_symbol_body` is too broad):
```
replace_content(needle="old_pattern.*?end", repl="new_content", mode="regex")
```
Use non-greedy `.*?` to avoid matching too much.

### Keep Memories Updated
After significant work, update memories with `write_memory` so future sessions have context. Review `.serena/memories/` periodically and keep them current.

### Think Tools Are Your Friends
Use `think_about_collected_information` after research and `think_about_task_adherence` before making edits. These help maintain focus on complex tasks.
