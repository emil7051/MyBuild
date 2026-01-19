"""Add indexes for session and analytics query performance

Revision ID: 003
Revises: 002
Create Date: 2025-01-19

This migration adds indexes to improve query performance for:
- Session lookups by session_id in calculation_results and user_inputs
- Analytics queries that filter by vehicle_id and created_at
- Time-based queries on sessions

Without these indexes, analytics queries must perform full table scans,
which degrades performance as the dataset grows.

This migration is IDEMPOTENT: skips indexes that already exist.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    """Get set of existing index names for a table."""
    return {idx["name"] for idx in inspector.get_indexes(table_name) if idx["name"]}


def upgrade() -> None:
    """Add performance indexes if they don't already exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Indexes on calculation_results table
    existing = _get_existing_indexes(inspector, "calculation_results")
    with op.batch_alter_table("calculation_results", schema=None) as batch_op:
        if "ix_calculation_results_session_id" not in existing:
            batch_op.create_index(
                "ix_calculation_results_session_id",
                ["session_id"],
                unique=False,
            )
        if "ix_calculation_results_vehicle_id" not in existing:
            batch_op.create_index(
                "ix_calculation_results_vehicle_id",
                ["vehicle_id"],
                unique=False,
            )
        if "ix_calculation_results_created_at" not in existing:
            batch_op.create_index(
                "ix_calculation_results_created_at",
                ["created_at"],
                unique=False,
            )
        # Composite index for analytics aggregation queries
        if "ix_calculation_results_analytics" not in existing:
            batch_op.create_index(
                "ix_calculation_results_analytics",
                ["session_id", "vehicle_id", "created_at"],
                unique=False,
            )

    # Indexes on user_inputs table
    existing = _get_existing_indexes(inspector, "user_inputs")
    with op.batch_alter_table("user_inputs", schema=None) as batch_op:
        if "ix_user_inputs_session_id" not in existing:
            batch_op.create_index(
                "ix_user_inputs_session_id",
                ["session_id"],
                unique=False,
            )
        if "ix_user_inputs_vehicle_id" not in existing:
            batch_op.create_index(
                "ix_user_inputs_vehicle_id",
                ["vehicle_id"],
                unique=False,
            )

    # Indexes on sessions table for time-based queries
    existing = _get_existing_indexes(inspector, "sessions")
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        if "ix_sessions_created_at" not in existing:
            batch_op.create_index(
                "ix_sessions_created_at",
                ["created_at"],
                unique=False,
            )
        if "ix_sessions_status" not in existing:
            batch_op.create_index(
                "ix_sessions_status",
                ["status"],
                unique=False,
            )


def downgrade() -> None:
    """Remove performance indexes."""
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_sessions_status")
        batch_op.drop_index("ix_sessions_created_at")

    with op.batch_alter_table("user_inputs", schema=None) as batch_op:
        batch_op.drop_index("ix_user_inputs_vehicle_id")
        batch_op.drop_index("ix_user_inputs_session_id")

    with op.batch_alter_table("calculation_results", schema=None) as batch_op:
        batch_op.drop_index("ix_calculation_results_analytics")
        batch_op.drop_index("ix_calculation_results_created_at")
        batch_op.drop_index("ix_calculation_results_vehicle_id")
        batch_op.drop_index("ix_calculation_results_session_id")
