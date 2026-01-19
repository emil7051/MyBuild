"""Initial schema baseline

Revision ID: 001
Revises: None
Create Date: 2025-01-19

This migration represents the initial database schema.
It creates all tables as they existed before the migration system was introduced.
Running this migration on an empty database will create the full schema.
Running it on an existing database will be a no-op (tables already exist).
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
    """Create initial schema tables."""
    # Sessions table
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
