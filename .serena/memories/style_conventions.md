# Style and conventions (updated 2026-02-06)

Python:
- 4-space indents, type hints, Google-style docstrings.
- Format/lint with: `ruff check .`, `black .`, `isort .`.
- Type-check scope used in CI: `mypy backend/app/core backend/app/api backend/app/main.py`.

TypeScript:
- Strict mode, ESLint flat config (`frontend/eslint.config.js`), 2-space indent, single quotes.
- Components use PascalCase; hooks use useCamelCase.
- Import DTOs/contracts from `shared/types`.

Package/dependency workflow:
- Use `bun` for frontend commands.
- Prefer `bun install --frozen-lockfile` for reproducible installs.

Config/data workflow:
- Use `.env.example` as template and load env via `python-dotenv` / `pydantic-settings`.
- Regenerate shared data/types when `data/*.py` changes: `python scripts/generate_vehicle_catalog_ts.py`.
- Validate data changes with: `python scripts/validation.py`.