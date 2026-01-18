# Suggested commands

Quick start:
- docker compose up --build
- python scripts/generate_vehicle_catalog_ts.py

Backend:
- python -m pip install -r requirements.txt
- uvicorn backend.app.main:app --reload

Frontend:
- cd frontend && npm install && npm run dev
- npm run build
- npm run lint
- npm run typecheck

Testing:
- python -m pytest tests --cov
- cd frontend && npm run test

Lint/format (Python):
- ruff check .
- black .
- isort .

Validation:
- python scripts/validation.py
