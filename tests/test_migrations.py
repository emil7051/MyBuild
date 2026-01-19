"""Tests for database migrations and schema integrity."""

from __future__ import annotations

from pathlib import Path
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from backend.app.db.models import (
    CalculationResultRecord,
    SessionRecord,
    UserInputRecord,
)


def get_test_alembic_config(db_path: str) -> Config:
    """Create Alembic config pointing to test database."""
    backend_dir = Path(__file__).parent.parent / "backend"
    alembic_ini = backend_dir / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


class TestMigrationSystem:
    """Tests for the Alembic migration system."""

    def test_alembic_config_loads(self) -> None:
        """Verify Alembic configuration can be loaded."""
        backend_dir = Path(__file__).parent.parent / "backend"
        alembic_ini = backend_dir / "alembic.ini"
        assert alembic_ini.exists(), "alembic.ini should exist in backend directory"

        config = Config(str(alembic_ini))
        assert config.get_main_option("script_location") == "alembic"

    def test_migrations_directory_exists(self) -> None:
        """Verify migration versions directory exists."""
        backend_dir = Path(__file__).parent.parent / "backend"
        versions_dir = backend_dir / "alembic" / "versions"
        assert versions_dir.exists(), "alembic/versions directory should exist"
        assert versions_dir.is_dir()

    def test_migrations_can_run_to_head(self) -> None:
        """Verify all migrations can run successfully on fresh database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            config = get_test_alembic_config(str(db_path))

            # Run migrations to head
            command.upgrade(config, "head")

            # Verify database was created and has expected tables
            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            assert "sessions" in tables
            assert "user_inputs" in tables
            assert "calculation_results" in tables
            assert "operator_profiles" in tables
            assert "feedback" in tables
            assert "alembic_version" in tables

    def test_migration_adds_session_secret_hash(self) -> None:
        """Verify session_secret_hash column is added by migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            config = get_test_alembic_config(str(db_path))

            command.upgrade(config, "head")

            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)
            columns = {c["name"] for c in inspector.get_columns("sessions")}

            assert (
                "session_secret_hash" in columns
            ), "session_secret_hash column should exist after migrations"

    def test_migration_adds_indexes(self) -> None:
        """Verify performance indexes are created by migrations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            config = get_test_alembic_config(str(db_path))

            command.upgrade(config, "head")

            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)

            # Check calculation_results indexes
            calc_indexes = {
                idx["name"] for idx in inspector.get_indexes("calculation_results")
            }
            assert "ix_calculation_results_session_id" in calc_indexes
            assert "ix_calculation_results_vehicle_id" in calc_indexes
            assert "ix_calculation_results_created_at" in calc_indexes
            assert "ix_calculation_results_analytics" in calc_indexes

            # Check user_inputs indexes
            input_indexes = {
                idx["name"] for idx in inspector.get_indexes("user_inputs")
            }
            assert "ix_user_inputs_session_id" in input_indexes
            assert "ix_user_inputs_vehicle_id" in input_indexes

            # Check sessions indexes
            session_indexes = {idx["name"] for idx in inspector.get_indexes("sessions")}
            assert "ix_sessions_created_at" in session_indexes
            assert "ix_sessions_status" in session_indexes


class TestModelIndexDefinitions:
    """Tests verifying indexes are defined in SQLAlchemy models."""

    def test_session_record_has_table_args_with_indexes(self) -> None:
        """Verify SessionRecord model defines indexes."""
        assert hasattr(SessionRecord, "__table_args__")
        table_args = SessionRecord.__table_args__
        index_names = {idx.name for idx in table_args if hasattr(idx, "name")}
        assert "ix_sessions_created_at" in index_names
        assert "ix_sessions_status" in index_names

    def test_user_input_record_has_table_args_with_indexes(self) -> None:
        """Verify UserInputRecord model defines indexes."""
        assert hasattr(UserInputRecord, "__table_args__")
        table_args = UserInputRecord.__table_args__
        index_names = {idx.name for idx in table_args if hasattr(idx, "name")}
        assert "ix_user_inputs_session_id" in index_names
        assert "ix_user_inputs_vehicle_id" in index_names

    def test_calculation_result_record_has_table_args_with_indexes(self) -> None:
        """Verify CalculationResultRecord model defines indexes."""
        assert hasattr(CalculationResultRecord, "__table_args__")
        table_args = CalculationResultRecord.__table_args__
        index_names = {idx.name for idx in table_args if hasattr(idx, "name")}
        assert "ix_calculation_results_session_id" in index_names
        assert "ix_calculation_results_vehicle_id" in index_names
        assert "ix_calculation_results_created_at" in index_names
        assert "ix_calculation_results_analytics" in index_names


class TestSessionSecretHashColumn:
    """Tests for the session_secret_hash column."""

    def test_session_record_has_secret_hash_column(self) -> None:
        """Verify SessionRecord model has session_secret_hash column."""
        column_names = {c.name for c in SessionRecord.__table__.columns}
        assert "session_secret_hash" in column_names

    def test_session_secret_hash_is_nullable(self) -> None:
        """Verify session_secret_hash allows null for backward compatibility."""
        column = SessionRecord.__table__.columns["session_secret_hash"]
        assert column.nullable is True

    def test_session_secret_hash_has_sufficient_length(self) -> None:
        """Verify session_secret_hash can store bcrypt hashes (60+ chars)."""
        column = SessionRecord.__table__.columns["session_secret_hash"]
        # Bcrypt hashes are 60 characters, allow extra for future algorithms
        assert column.type.length >= 60
