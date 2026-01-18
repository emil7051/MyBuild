# Style and conventions

Python:
- 4-space indents, type hints, Google-style docstrings.
- Format/lint with: ruff, black, isort.

TypeScript:
- Strict mode, ESLint/Prettier defaults (2-space indent, single quotes).
- Components use PascalCase; hooks use useCamelCase.
- Import DTOs from shared/types to keep contracts consistent.

Config/Env:
- Use .env.example as template; load env via python-dotenv / pydantic-settings.
- Regenerate shared types when data/*.py changes.
