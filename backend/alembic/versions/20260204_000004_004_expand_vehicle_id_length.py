"""Expand vehicle_id columns to 32 characters.

Revision ID: 004
Revises: 003
Create Date: 2026-02-04
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase vehicle_id length to 32 characters."""
    with op.batch_alter_table("user_inputs") as batch_op:
        batch_op.alter_column(
            "vehicle_id",
            existing_type=sa.String(16),
            type_=sa.String(32),
            nullable=False,
        )
    with op.batch_alter_table("calculation_results") as batch_op:
        batch_op.alter_column(
            "vehicle_id",
            existing_type=sa.String(16),
            type_=sa.String(32),
            nullable=False,
        )


def downgrade() -> None:
    """Revert vehicle_id length to 16 characters."""
    with op.batch_alter_table("user_inputs") as batch_op:
        batch_op.alter_column(
            "vehicle_id",
            existing_type=sa.String(32),
            type_=sa.String(16),
            nullable=False,
        )
    with op.batch_alter_table("calculation_results") as batch_op:
        batch_op.alter_column(
            "vehicle_id",
            existing_type=sa.String(32),
            type_=sa.String(16),
            nullable=False,
        )
