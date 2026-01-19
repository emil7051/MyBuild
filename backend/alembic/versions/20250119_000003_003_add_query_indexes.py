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
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    # Indexes on calculation_results table
    with op.batch_alter_table("calculation_results", schema=None) as batch_op:
        batch_op.create_index(
            "ix_calculation_results_session_id",
            ["session_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_calculation_results_vehicle_id",
            ["vehicle_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_calculation_results_created_at",
            ["created_at"],
            unique=False,
        )
        # Composite index for analytics aggregation queries
        batch_op.create_index(
            "ix_calculation_results_analytics",
            ["session_id", "vehicle_id", "created_at"],
            unique=False,
        )

    # Indexes on user_inputs table
    with op.batch_alter_table("user_inputs", schema=None) as batch_op:
        batch_op.create_index(
            "ix_user_inputs_session_id",
            ["session_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_user_inputs_vehicle_id",
            ["vehicle_id"],
            unique=False,
        )

    # Indexes on sessions table for time-based queries
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.create_index(
            "ix_sessions_created_at",
            ["created_at"],
            unique=False,
        )
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
