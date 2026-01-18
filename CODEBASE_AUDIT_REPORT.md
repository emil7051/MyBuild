# Codebase Audit Report

## Scope
- Reviewed documentation, backend, frontend, shared code, and scripts.
- Searched for TODO/FIXME markers, deprecated patterns, and unused/legacy code.
- Checked configuration, build, and test setup for drift or gaps.

## Findings

### Critical
- None found.

### Serious
- Backend tests are effectively absent despite documentation stating they exist. Only `tests/conftest.py` is present, so `pytest tests/ --cov` is misleading and provides no coverage. Evidence: `AGENTS.md:35`, `README.md:185`, `tests/conftest.py:1`.
- README suggests running `python -m backend.app.db.session` as a migration step, but that module has no CLI and performs no work on import. This masks the absence of real migrations. Evidence: `README.md:58`, `backend/app/db/session.py:1`.

### Minor
- Deprecated patterns are used: FastAPI `@app.on_event` and Pydantic v1 `@validator`. These will emit deprecation warnings and should be updated to lifespan events and `field_validator`. Evidence: `backend/app/main.py:30`, `backend/app/models/session.py:22`.
- Inconsistent overrides shape stored in `UserInputRecord.overrides` (nested when vehicle-specific overrides exist, flat otherwise), which complicates downstream consumers. Evidence: `backend/app/services/sessions.py:262`.

### Resolved This Pass
- Aligned `API.md` with current Pydantic schemas (session payload shape, duty cycle units, analytics fields).
- Removed references to missing deployment/troubleshooting docs to prevent dead links.
- Standardized frontend tooling on Bun and port 5000 across Docker and docs.
- Removed unused models/constants/config fields tied to legacy flows.
- Split and pinned Python requirements; updated `.gitignore` for Playwright artifacts.

## Suggested Remediations (Open)
- Add a backend test suite (or adjust docs to reflect current state).
- Introduce a migration tool (e.g., Alembic) and update README to use it instead of a no-op module import.
- Replace deprecated FastAPI/Pydantic patterns with lifespan events and `field_validator`.
- Normalize overrides persistence to a consistent shape for downstream consumers.
