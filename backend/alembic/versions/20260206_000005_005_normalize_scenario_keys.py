"""Normalize stored scenario identifiers to canonical scenario keys.

Revision ID: 005
Revises: 004
Create Date: 2026-02-06
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize_table_scenarios(table_name: str) -> None:
    op.execute(
        f"""
        UPDATE {table_name}
        SET scenario_name = CASE
            WHEN lower(trim(scenario_name)) = 'baseline' THEN 'baseline'
            WHEN lower(trim(scenario_name)) = 'technology breakthrough'
                THEN 'technology_breakthrough'
            WHEN lower(trim(scenario_name)) = 'oil crisis' THEN 'oil_crisis'
            ELSE scenario_name
        END
        """
    )


def upgrade() -> None:
    """Backfill historical rows so scenario_name always stores scenario keys."""
    _normalize_table_scenarios("calculation_results")
    _normalize_table_scenarios("user_inputs")


def downgrade() -> None:
    """No-op: conversion to canonical keys is intentionally irreversible."""
    return None
