"""Initial schema baseline

Revision ID: 001
Revises: None
Create Date: 2025-01-19

This migration represents the initial database schema.
It creates all tables as they existed before the migration system was introduced.

This migration is IDEMPOTENT:
- On an empty database: creates all tables
- On an existing database: skips tables that already exist (safe no-op)

This allows databases created before Alembic was introduced to be safely
migrated to the Alembic-managed schema without manual intervention.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema tables if they don't already exist.

    This migration is idempotent: it checks for existing tables before creating.
    This handles the case where the database was set up before Alembic was
    introduced, allowing safe migration to the Alembic-managed schema.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Sessions table
    if "sessions" not in existing_tables:
        op.create_table(
            "sessions",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("wizard_state", sa.JSON(), nullable=True),
            sa.Column("cached_results", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # User inputs table
    if "user_inputs" not in existing_tables:
        op.create_table(
            "user_inputs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(36), nullable=False),
            sa.Column("vehicle_id", sa.String(16), nullable=False),
            sa.Column("scenario_name", sa.String(64), nullable=False),
            sa.Column("purchase_method", sa.String(16), nullable=False),
            sa.Column("overrides", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )

    # Calculation results table
    if "calculation_results" not in existing_tables:
        op.create_table(
            "calculation_results",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(36), nullable=False),
            sa.Column("vehicle_id", sa.String(16), nullable=False),
            sa.Column("scenario_name", sa.String(64), nullable=False),
            sa.Column("purchase_method", sa.String(16), nullable=False),
            sa.Column("result_payload", sa.JSON(), nullable=False),
            sa.Column("total_cost", sa.Float(), nullable=False),
            sa.Column("annual_cost", sa.Float(), nullable=False),
            sa.Column("cost_per_km", sa.Float(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )

    # Operator profiles table
    if "operator_profiles" not in existing_tables:
        op.create_table(
            "operator_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(36), nullable=False),
            sa.Column("operator_type", sa.String(64), nullable=True),
            sa.Column("fleet_size", sa.String(32), nullable=True),
            sa.Column("contact_email", sa.String(255), nullable=True),
            sa.Column(
                "consent_to_contact", sa.Boolean(), nullable=False, server_default="0"
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("session_id"),
        )

    # Feedback table
    if "feedback" not in existing_tables:
        op.create_table(
            "feedback",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.String(36), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("feedback")
    op.drop_table("operator_profiles")
    op.drop_table("calculation_results")
    op.drop_table("user_inputs")
    op.drop_table("sessions")
