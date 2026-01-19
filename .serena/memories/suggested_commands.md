# Suggested Commands

**Note**: Use `bun` instead of `npm` per project conventions.

---

# Suggested commands

Quick start:
- docker compose up --build
- python scripts/generate_vehicle_catalog_ts.py

Backend:
- python -m pip install -r requirements.txt
- uvicorn backend.app.main:app --reload

Frontend:
- cd frontend && bun install && bun run dev
- bun run build
- bun run lint
- bun run typecheck

Testing:
- python -m pytest tests --cov
- cd frontend && bun run test

Lint/format (Python):
- ruff check .
- black .
- isort .

Validation:
- python scripts/validation.py
