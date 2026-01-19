"""Add session_secret_hash column for access control

Revision ID: 002
Revises: 001
Create Date: 2025-01-19

This migration adds the session_secret_hash column to the sessions table.
This column stores a bcrypt hash of a per-session access secret, enabling
session access control where knowing the sessionId alone is not sufficient
to read or update session data containing PII.

The column is nullable to support existing sessions created before this
security enhancement. New sessions will have a secret generated on creation.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add session_secret_hash column to sessions table."""
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "session_secret_hash",
                sa.String(128),
                nullable=True,
                comment="Bcrypt hash of session access secret for PII protection",
            )
        )


def downgrade() -> None:
    """Remove session_secret_hash column from sessions table."""
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.drop_column("session_secret_hash")
