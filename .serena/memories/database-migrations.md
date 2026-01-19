# Database Migrations System

## Overview
The TCO Web Platform uses Alembic for database schema migrations, implemented in Phase 4 Stream A2 (January 2025).

## Directory Structure
```
backend/
├── alembic.ini           # Alembic configuration
└── alembic/
    ├── env.py            # Migration environment (async-aware)
    ├── script.py.mako    # Migration template
    └── versions/         # Migration files
        ├── 20250119_000001_001_initial_schema.py
        ├── 20250119_000002_002_add_session_secret_hash.py
        └── 20250119_000003_003_add_query_indexes.py
```

## Key Features
- Supports both SQLite (development) and PostgreSQL (production)
- Uses batch mode for SQLite ALTER TABLE operations
- Migrations run automatically on app startup via `init_db()`
- URL can be overridden via config for testing

## Running Migrations
```bash
cd backend
alembic upgrade head      # Apply all pending
alembic current           # Check current version
alembic history           # View migration history
alembic downgrade -1      # Rollback one
```

## Creating New Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"  # Auto-detect changes
alembic revision -m "Description"                  # Empty migration
```

## Important Notes
- Always review auto-generated migrations before applying
- Migrations are designed to be safe for existing data
- Tests in `tests/test_migrations.py` verify migration integrity
- The `session_secret_hash` column prepares for SEC-005 (session access control)
- Performance indexes support analytics queries (API-006)

## Related Tasks
- DB-001: Migration mechanism
- DB-002: session_secret_hash column
- DB-003: Performance indexes
- SEC-005: Session access control (uses session_secret_hash)
- API-006: Analytics SQL optimization (uses indexes)
