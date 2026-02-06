"""Tests for policy calculation helpers."""

from __future__ import annotations

import pytest

from data.policies import POLICIES, calculate_bev_purchase_rebate


@pytest.fixture(autouse=True)
def restore_rebate_policy_state():
    """Reset mutable global policy config between tests."""
    purchase_rebate = POLICIES["purchase_rebate"]
    percentage_rebate = POLICIES["percentage_rebate"]

    snapshot = {
        "purchase_enabled": purchase_rebate.enabled,
        "purchase_amount": purchase_rebate.amount,
        "percentage_enabled": percentage_rebate.enabled,
        "percentage_rate": percentage_rebate.percentage,
        "percentage_cap": percentage_rebate.max_amount,
    }

    yield

    purchase_rebate.enabled = snapshot["purchase_enabled"]
    purchase_rebate.amount = snapshot["purchase_amount"]
    percentage_rebate.enabled = snapshot["percentage_enabled"]
    percentage_rebate.percentage = snapshot["percentage_rate"]
    percentage_rebate.max_amount = snapshot["percentage_cap"]


def test_bev_purchase_rebate_applies_fixed_before_percentage() -> None:
    POLICIES["purchase_rebate"].enabled = True
    POLICIES["purchase_rebate"].amount = 20_000
    POLICIES["percentage_rebate"].enabled = True
    POLICIES["percentage_rebate"].percentage = 0.10
    POLICIES["percentage_rebate"].max_amount = None

    # 20,000 fixed + 10% of (100,000 - 20,000) = 8,000
    assert calculate_bev_purchase_rebate(100_000) == 28_000


def test_bev_purchase_rebate_clamps_percentage_base_to_zero() -> None:
    POLICIES["purchase_rebate"].enabled = True
    POLICIES["purchase_rebate"].amount = 20_000
    POLICIES["percentage_rebate"].enabled = True
    POLICIES["percentage_rebate"].percentage = 0.10
    POLICIES["percentage_rebate"].max_amount = None

    # Fixed rebate exceeds price, so percentage component should be zero.
    assert calculate_bev_purchase_rebate(15_000) == 20_000
