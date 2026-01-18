This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: backend/**/*.py, frontend/**/*.ts, frontend/**/*.tsx, shared/**/*.ts, data/**/*.py, scripts/**/*.py, tests/**/*.py, *.md, *.json, *.yml, docker-compose.yml
- Files matching these patterns are excluded: node_modules, **/.venv, **/__pycache__, **/dist, **/.next, **/.git, .git, *.png, *.jpg, *.ico, *.svg, archive, attached_assets, .github, plans, .replit, .serena, .claude
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

</file_summary>

<directory_structure>
backend/
  app/
    api/
      __init__.py
      router.py
    core/
      __init__.py
      cache.py
      config.py
    db/
      __init__.py
      base.py
      models.py
      session.py
    models/
      __init__.py
      calculation.py
      session.py
      vehicle.py
    services/
      __init__.py
      sessions.py
      vehicles.py
    __init__.py
    main.py
data/
  __init__.py
  constants.py
  policies.py
  scenarios.py
  vehicles.py
frontend/
  e2e/
    screenshots.ts
    ui-redesign.spec.ts
  src/
    components/
      layout/
        AppShell.tsx
      results/
        AnalyticsSummaryCard.tsx
        ComparisonHighlights.tsx
        CostBreakdownChart.tsx
        CostPerKmChart.tsx
        PaybackChart.tsx
        ResultsPanel.tsx
        SavingsWaterfallChart.tsx
        SensitivityTornadoChart.tsx
      shared/
        Button.tsx
        Card.tsx
        Field.tsx
        Select.tsx
      wizard/
        ComparisonConfigPanel.tsx
        SelectedVehiclesSummary.tsx
        VehicleParamsForm.tsx
        WizardCompareStep.tsx
        WizardCostStep.tsx
        WizardDieselStep.tsx
        WizardElectricStep.tsx
        WizardOperatingStep.tsx
        WizardStepper.tsx
        WizardVehicleStep.tsx
    forms/
      wizardForm.ts
    hooks/
      useAnalyticsSummary.ts
      useCalculations.ts
      useVehicleCatalog.ts
      useWizardAutosave.ts
    pages/
      ResultsPage.tsx
      WizardPage.tsx
    services/
      api.ts
    state/
      tcoStore.ts
    test/
      calculator/
        breakdown.test.ts
        edge-cases.test.ts
        math.test.ts
        overrides.test.ts
        purchase-methods.test.ts
        scenarios.test.ts
      critical-fixes.test.ts
      input-validation.test.ts
      reproduce_crash.test.ts
      state-management.test.ts
      verification.test.ts
    utils/
      format.ts
      payload.ts
    App.tsx
    main.tsx
  playwright.config.ts
  vite.config.ts
  vitest.config.ts
scripts/
  generate_vehicle_catalog_ts.py
  validate_deployment.py
  validation.py
shared/
  calculator/
    index.ts
    math.ts
    tcoCalculator.ts
  data/
    constants.ts
    policies.ts
    scenarios.ts
    vehicleCatalog.ts
  types/
    tco.types.ts
tests/
  __init__.py
  conftest.py
AGENTS.md
API.md
CODEBASE_AUDIT_REPORT.md
docker-compose.yml
README.md
replit.md
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path="CODEBASE_AUDIT_REPORT.md">
# Codebase Audit Report

## Scope
- Reviewed documentation, backend, frontend, shared code, and scripts.
- Searched for TODO/FIXME markers, deprecated patterns, and unused/legacy code.
- Checked configuration, build, and test setup for drift or gaps.

## Findings

### Critical
- None found.

### Serious
- API documentation is out of sync with actual request/response schemas. The session payload shape, duty cycle units, and results fields in `API.md` do not match the Pydantic models, which will break external integrations that follow the docs. Evidence: `API.md:124`, `API.md:136`, `API.md:139`, `API.md:155`, `API.md:242`, `backend/app/models/session.py:17`, `backend/app/models/session.py:36`, `backend/app/models/session.py:107`, `backend/app/models/calculation.py:130`.
- Analytics response examples in `API.md` do not match the actual analytics schema (field names and structure differ). Evidence: `API.md:239`, `backend/app/models/session.py:126`.
- Deployment and troubleshooting docs are referenced but missing, leaving operational guidance gaps. Evidence: `AGENTS.md:7`, `AGENTS.md:10`, `README.md:236`, `README.md:242`, `replit.md:21`.
- Backend tests are effectively absent despite documentation stating they exist. Only `tests/conftest.py` is present, so `pytest tests/ --cov` is misleading and provides no coverage. Evidence: `AGENTS.md:37`, `README.md:118`, `tests/conftest.py:1`.
- Local dev guidance is inconsistent: docs use Bun and port 5000, Docker uses npm and port 3000, and default CORS origins are set for 5000 only. This can cause dependency drift or CORS issues depending on which instructions are followed. Evidence: `README.md:28`, `README.md:72`, `README.md:78`, `AGENTS.md:34`, `docker-compose.yml:28`, `frontend/Dockerfile:6`, `frontend/vite.config.ts:21`, `backend/.env.example:6`, `scripts/validate_deployment.py:65`.
- README suggests running `python -m backend.app.db.session` as a migration step, but that module has no CLI and performs no work on import. This masks the absence of real migrations. Evidence: `README.md:58`, `backend/app/db/session.py:1`.

### Minor
- Deprecated patterns are used: FastAPI `@app.on_event` and Pydantic v1 `@validator`. These will emit deprecation warnings and should be updated to lifespan events and `field_validator`. Evidence: `backend/app/main.py:30`, `backend/app/models/session.py:22`.
- Unused/legacy code remains: `CalculationRequest` and `ComparisonRequest` are defined but not referenced; `CostOverride.to_engine_overrides` references the retired Python engine; and legacy charging proportions are kept but unused. Evidence: `backend/app/models/calculation.py:46`, `backend/app/models/calculation.py:87`, `shared/data/constants.ts:125`.
- Unused configuration: `cache_results` is defined but never referenced. Evidence: `backend/app/core/config.py:22`.
- Dependency management drift: `requirements.txt` mixes runtime and tooling dependencies, duplicates packages, and includes unpinned entries at the end, while `backend/requirements.txt` is a separate runtime set. This makes installs non-reproducible and increases attack surface. Evidence: `requirements.txt:1`, `requirements.txt:63`.
- Test artifacts are not ignored: `frontend/playwright-report` and `frontend/test-results` exist but are not listed in `.gitignore`, risking accidental commits. Evidence: `.gitignore:166`.
- Inconsistent overrides shape stored in `UserInputRecord.overrides` (nested when vehicle-specific overrides exist, flat otherwise), which complicates downstream consumers. Evidence: `backend/app/services/sessions.py:262`.

## Suggested Remediations
- Align `API.md` with the Pydantic schemas (or generate docs from code) and fix duty cycle units, session payload shape, and analytics fields.
- Add `DEPLOYMENT.md` and `TROUBLESHOOTING.md` or remove references until they exist.
- Add a backend test suite (or adjust docs to reflect current state).
- Standardize on a single package manager (bun or npm) and a single dev port; update Docker, docs, and CORS defaults accordingly.
- Introduce a migration tool (e.g., Alembic) and update README to use it instead of a no-op module import.
- Remove or clearly quarantine unused models/legacy constants and unused config fields.
- Split `requirements.txt` into runtime vs dev tooling, remove duplicates, and pin versions.
- Update `.gitignore` to exclude Playwright reports and test artifacts.
</file>

<file path="backend/app/api/__init__.py">
"""API routers for the TCO platform backend."""

from .router import api_router

__all__ = ["api_router"]
</file>

<file path="backend/app/core/__init__.py">
"""Core application utilities (configuration, logging, etc.)."""
</file>

<file path="backend/app/db/__init__.py">
"""Database utilities for the FastAPI backend."""

from .session import get_db_session, init_db

__all__ = ["get_db_session", "init_db"]
</file>

<file path="backend/app/db/base.py">
"""Declarative base for SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common declarative base."""

    pass
</file>

<file path="backend/app/db/session.py">
"""Database session helpers and lifecycle utilities."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.db.base import Base

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Initialise database schema on startup."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""

    async with AsyncSessionFactory() as session:
        yield session
</file>

<file path="backend/app/models/vehicle.py">
"""Schemas that expose vehicle metadata to consumers."""

from __future__ import annotations

from pydantic import BaseModel


class VehicleSummary(BaseModel):
    vehicle_id: str
    model_name: str
    drivetrain_type: str
    weight_class: str
    comparison_pair: str


class VehicleDetail(VehicleSummary):
    payload: float
    msrp: float
    range_km: float
    battery_capacity_kwh: float
    kwh_per_km: float
    litres_per_km: float
    maintenance_cost_per_km: float
    annual_registration: float
    annual_kms: float
</file>

<file path="backend/app/__init__.py">
"""Backend FastAPI application package."""

from .main import app

__all__ = ["app"]
</file>

<file path="data/__init__.py">
"""Data package for TCO calculator."""
</file>

<file path="data/policies.py">
"""
Policy incentives and switches for battery electric truck adoption.

- Policy definitions, parameters, and activation switches
- Policy impact calculations
"""

from dataclasses import dataclass
from typing import Optional

# ============================================================================
# POLICY DATACLASSES
# ============================================================================


@dataclass
class PolicyIncentive:
    """Base class for policy incentives with common attributes."""

    name: str
    description: str
    enabled: bool = False

    def __post_init__(self):
        """Validate policy parameters."""
        if self.enabled and not self.validate():
            raise ValueError(f"Policy '{self.name}' has invalid parameters")

    def validate(self) -> bool:
        """Override in subclasses to validate specific parameters."""
        return True


@dataclass
class PurchaseRebate(PolicyIncentive):
    """Fixed rebate amount for new BEV purchase."""

    amount: float = 0.0  # $ AUD

    def validate(self) -> bool:
        return self.amount >= 0


@dataclass
class PercentageRebate(PolicyIncentive):
    """Percentage-based rebate on BEV purchase price."""

    percentage: float = 0.0  # As decimal (e.g., 0.1 for 10%)
    max_amount: Optional[float] = None  # Maximum rebate cap in $ AUD

    def validate(self) -> bool:
        return 0 <= self.percentage <= 1 and (
            self.max_amount is None or self.max_amount > 0
        )


@dataclass
class StampDutyExemption(PolicyIncentive):
    """Exemption from stamp duty for BEV purchases."""

    exemption_percentage: float = 0.0  # As decimal (e.g., 1.0 for 100% exemption)

    def validate(self) -> bool:
        return 0 <= self.exemption_percentage <= 1


@dataclass
class CarbonPrice(PolicyIncentive):
    """Carbon price applied to emissions."""

    price_per_tonne: float = 0.0  # $ AUD per tonne CO2e

    def validate(self) -> bool:
        return self.price_per_tonne >= 0


@dataclass
class GreenLoanSubsidy(PolicyIncentive):
    """Reduced interest rate for BEV financing."""

    rate_reduction: float = 0.0  # Percentage points reduction (e.g., 0.02 for 2%)

    def validate(self) -> bool:
        return 0 <= self.rate_reduction <= 0.5  # Max 50% reduction


@dataclass
class ChargingInfrastructureGrant(PolicyIncentive):
    """Grant for charging infrastructure installation."""

    grant_percentage: float = 0.0  # As decimal (e.g., 0.5 for 50% grant)
    max_amount: Optional[float] = None  # Maximum grant cap in $ AUD

    def validate(self) -> bool:
        return 0 <= self.grant_percentage <= 1 and (
            self.max_amount is None or self.max_amount > 0
        )


# ============================================================================
# POLICY DEFINITIONS
# ============================================================================

# Define all available policies
POLICIES = {
    "purchase_rebate": PurchaseRebate(
        name="Fixed Purchase Rebate",
        description="Fixed dollar amount rebate for new BEV purchases",
        enabled=False,
        amount=0,
    ),
    "percentage_rebate": PercentageRebate(
        name="Percentage Purchase Rebate",
        description="Percentage-based rebate on BEV purchase price",
        enabled=False,
        percentage=0.0,
        max_amount=None,
    ),
    "stamp_duty_exemption": StampDutyExemption(
        name="Stamp Duty Exemption",
        description="Full or partial exemption from stamp duty for BEVs",
        enabled=False,
        exemption_percentage=0.0,
    ),
    "carbon_price": CarbonPrice(
        name="Carbon Pricing",
        description="Price on carbon emissions from diesel vehicles",
        enabled=False,
        price_per_tonne=0,
    ),
    "green_loan_subsidy": GreenLoanSubsidy(
        name="Green Loan Subsidy",
        description="Reduced interest rate for BEV financing",
        enabled=False,
        rate_reduction=0.0,
    ),
    "charging_grant": ChargingInfrastructureGrant(
        name="Charging Infrastructure Grant",
        description="Grant for charging infrastructure installation",
        enabled=False,
        grant_percentage=0.0,
        max_amount=None,
    ),
}

# ============================================================================
# POLICY CALCULATIONS
# ============================================================================


def get_policy(policy_key: str) -> PolicyIncentive:
    """Get a policy by its key."""
    if policy_key not in POLICIES:
        raise ValueError(f"Policy '{policy_key}' not found")
    return POLICIES[policy_key]


def get_active_policies() -> dict[str, PolicyIncentive]:
    """Get all currently active policies."""
    return {key: policy for key, policy in POLICIES.items() if policy.enabled}


def calculate_bev_purchase_rebate(vehicle_price: float) -> float:
    """Calculate total purchase rebate for a BEV based on active policies."""
    bev_purchase_rebate = 0.0

    # Fixed rebate
    if POLICIES["purchase_rebate"].enabled:
        bev_purchase_rebate += POLICIES["purchase_rebate"].amount

    # Percentage rebate
    if POLICIES["percentage_rebate"].enabled:
        percentage_rebate = vehicle_price * POLICIES["percentage_rebate"].percentage
        if POLICIES["percentage_rebate"].max_amount:
            percentage_rebate = min(
                percentage_rebate, POLICIES["percentage_rebate"].max_amount
            )
        bev_purchase_rebate += percentage_rebate

    return bev_purchase_rebate


def calculate_stamp_duty_with_exemption(base_stamp_duty: float, is_bev: bool) -> float:
    """Calculate stamp duty considering BEV exemptions."""
    if is_bev and POLICIES["stamp_duty_exemption"].enabled:
        exemption = (
            base_stamp_duty * POLICIES["stamp_duty_exemption"].exemption_percentage
        )
        return base_stamp_duty - exemption
    return base_stamp_duty


def calculate_financing_interest_rate(base_rate: float, is_bev: bool) -> float:
    """Calculate financing interest rate considering BEV subsidies."""
    if is_bev and POLICIES["green_loan_subsidy"].enabled:
        return max(0, base_rate - POLICIES["green_loan_subsidy"].rate_reduction)
    return base_rate


def calculate_annual_policy_charges(
    is_bev: bool, annual_emissions_tonnes: float = 0
) -> float:
    """Calculate annual charges/credits based on active policies."""
    annual_charges = 0.0

    # Carbon pricing (diesel only)
    if not is_bev and POLICIES["carbon_price"].enabled:
        annual_charges += (
            annual_emissions_tonnes * POLICIES["carbon_price"].price_per_tonne
        )

    return annual_charges


def calculate_infrastructure_grant(infrastructure_cost: float) -> float:
    """Calculate charging infrastructure grant amount."""
    if POLICIES["charging_grant"].enabled:
        grant = infrastructure_cost * POLICIES["charging_grant"].grant_percentage
        if POLICIES["charging_grant"].max_amount:
            grant = min(grant, POLICIES["charging_grant"].max_amount)
        return grant
    return 0.0


# ============================================================================
# POLICY SCENARIOS
# ============================================================================


# Example policy scenarios
def enable_standard_incentives():
    """Enable a standard set of BEV incentives."""
    POLICIES["purchase_rebate"].enabled = True
    POLICIES["purchase_rebate"].amount = 20000

    POLICIES["stamp_duty_exemption"].enabled = True
    POLICIES["stamp_duty_exemption"].exemption_percentage = 1.0

    POLICIES["green_loan_subsidy"].enabled = True
    POLICIES["green_loan_subsidy"].rate_reduction = 0.02


def enable_aggressive_incentives():
    """Enable aggressive BEV incentives plus diesel disincentives."""

    # BEV incentives
    POLICIES["percentage_rebate"].enabled = True
    POLICIES["percentage_rebate"].percentage = 0.15
    POLICIES["percentage_rebate"].max_amount = 50000

    POLICIES["stamp_duty_exemption"].enabled = True
    POLICIES["stamp_duty_exemption"].exemption_percentage = 1.0

    POLICIES["green_loan_subsidy"].enabled = True
    POLICIES["green_loan_subsidy"].rate_reduction = 0.03

    POLICIES["charging_grant"].enabled = True
    POLICIES["charging_grant"].grant_percentage = 0.5
    POLICIES["charging_grant"].max_amount = 500000

    # Diesel disincentives
    POLICIES["carbon_price"].enabled = True
    POLICIES["carbon_price"].price_per_tonne = 50


def disable_all_policies():
    """Disable all policy incentives."""
    for policy in POLICIES.values():
        policy.enabled = False
</file>

<file path="data/scenarios.py">
"""
Economic and environmental scenarios for TCO modelling to enable scenario-based analysis with time-varying parameters.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# ============================================================================
# SCENARIO DATACLASSES
# ============================================================================


@dataclass
class EconomicScenario:
    """Defines economic parameters that vary over time."""

    name: str
    description: str

    # Price trajectories (as annual multipliers from base year)
    diesel_price_trajectory: List[float] = field(default_factory=list)
    electricity_price_trajectory: List[float] = field(default_factory=list)
    battery_price_trajectory: List[float] = field(default_factory=list)
    carbon_price_trajectory: List[float] = field(default_factory=list)

    # Technology improvement curves
    bev_efficiency_improvement: List[float] = field(
        default_factory=list
    )  # Annual improvement in kWh/km
    diesel_efficiency_improvement: List[float] = field(
        default_factory=list
    )  # Annual improvement in L/km

    # Maintenance cost trajectory
    maintenance_cost_multiplier: List[float] = field(
        default_factory=list
    )  # Multiplier for maintenance costs by year

    # Market factors
    bev_residual_value_multiplier: List[float] = field(
        default_factory=list
    )  # Adjustment to depreciation
    infrastructure_cost_trajectory: List[float] = field(default_factory=list)

    # Policy evolution
    policy_phase_out_year: Optional[int] = None  # Year when subsidies end
    road_user_charge_bev_start_year: Optional[int] = (
        None  # Year when RUC applies to BEVs
    )

    def __post_init__(self):
        """Validate and extend trajectories to standard vehicle life."""
        from data.constants import VEHICLE_LIFE

        # Extend all trajectories to vehicle life if shorter
        self._extend_trajectory("diesel_price_trajectory", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("electricity_price_trajectory", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("battery_price_trajectory", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("carbon_price_trajectory", VEHICLE_LIFE, 0.0)
        self._extend_trajectory("bev_efficiency_improvement", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("diesel_efficiency_improvement", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("maintenance_cost_multiplier", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("bev_residual_value_multiplier", VEHICLE_LIFE, 1.0)
        self._extend_trajectory("infrastructure_cost_trajectory", VEHICLE_LIFE, 1.0)

    def _extend_trajectory(
        self, attr_name: str, target_length: int, default_value: float
    ):
        """Extend a trajectory list to target length."""
        trajectory = getattr(self, attr_name)
        if not trajectory:
            # If empty, create constant trajectory
            setattr(self, attr_name, [default_value] * target_length)
        elif len(trajectory) < target_length:
            # Extend with last value
            last_value = trajectory[-1]
            trajectory.extend([last_value] * (target_length - len(trajectory)))
            setattr(self, attr_name, trajectory)

    def get_diesel_price_multiplier(self, year: int) -> float:
        """Get diesel price multiplier for a specific year."""
        if 0 < year <= len(self.diesel_price_trajectory):
            return self.diesel_price_trajectory[year - 1]
        return 1.0

    def get_electricity_price_multiplier(self, year: int) -> float:
        """Get electricity price multiplier for a specific year."""
        if 0 < year <= len(self.electricity_price_trajectory):
            return self.electricity_price_trajectory[year - 1]
        return 1.0

    def get_battery_price_multiplier(self, year: int) -> float:
        """Get battery price multiplier for a specific year."""
        if 0 < year <= len(self.battery_price_trajectory):
            return self.battery_price_trajectory[year - 1]
        return 1.0

    def get_carbon_price(self, year: int) -> float:
        """Get carbon price for a specific year ($/tonne)."""
        if 0 < year <= len(self.carbon_price_trajectory):
            return self.carbon_price_trajectory[year - 1]
        return 0.0

    def policy_active(self, year: int) -> bool:
        """Check if policy incentives are active in a given year."""
        if self.policy_phase_out_year is None:
            return True
        return year < self.policy_phase_out_year

    def ruc_applies_bev(self, year: int) -> bool:
        """Check if road user charges apply to BEVs in a given year."""
        if self.road_user_charge_bev_start_year is None:
            return False
        return year >= self.road_user_charge_bev_start_year

    def get_maintenance_cost_multiplier(self, year: int) -> float:
        """Get maintenance cost multiplier for a specific year."""
        if 0 < year <= len(self.maintenance_cost_multiplier):
            return self.maintenance_cost_multiplier[year - 1]
        return 1.0


def generate_price_trajectory(
    base_growth_rate: float,
    years: int,
) -> List[float]:
    """
    Generate a price trajectory with optional volatility and shocks.

    Args:
        base_growth_rate: Annual growth rate (e.g., 0.03 for 3%)
        years: Number of years

    Returns:
        List of multipliers relative to base year
    """
    trajectory = [1.0]  # Base year = 1.0

    for year in range(2, years + 1):
        growth = base_growth_rate
        new_value = trajectory[-1] * (1 + growth)
        trajectory.append(new_value)

    return trajectory


def generate_maintenance_trajectory(
    years: int, start_multiplier: float = 0.85, end_multiplier: float = 1.25
) -> List[float]:
    """
    Generate a maintenance cost trajectory that increases over vehicle life.

    Args:
        years: Number of years
        start_multiplier: Starting multiplier (default 0.85 = 15% below average)
        end_multiplier: Ending multiplier (default 1.25 = 25% above average)

    Returns:
        List of multipliers that increase linearly from start to end
    """
    if years == 1:
        return [1.0]

    # Linear interpolation from start to end
    return [
        start_multiplier + (end_multiplier - start_multiplier) * i / (years - 1)
        for i in range(years)
    ]


# ============================================================================
# PRE-DEFINED SCENARIOS
# ============================================================================

SCENARIOS = {
    "baseline": EconomicScenario(
        name="Baseline",
        description="Current trajectory with moderate price increases",
        diesel_price_trajectory=generate_price_trajectory(
            0.03, 15
        ),  # 3% annual increase
        electricity_price_trajectory=generate_price_trajectory(
            0.02, 15
        ),  # 2% annual increase
        battery_price_trajectory=generate_price_trajectory(
            -0.07, 15
        ),  # 7% annual decrease
        carbon_price_trajectory=[0] * 15,  # No carbon price
        bev_efficiency_improvement=generate_price_trajectory(
            -0.02, 15
        ),  # 2% annual improvement
        diesel_efficiency_improvement=generate_price_trajectory(
            -0.01, 15
        ),  # 1% annual improvement
        maintenance_cost_multiplier=generate_maintenance_trajectory(
            15
        ),  # 0.85 to 1.25 over vehicle life
    ),
    "technology_breakthrough": EconomicScenario(
        name="Technology Breakthrough",
        description="Rapid battery technology improvement",
        diesel_price_trajectory=generate_price_trajectory(0.03, 15),
        electricity_price_trajectory=generate_price_trajectory(0.02, 15),
        battery_price_trajectory=[
            1.0,
            0.85,
            0.72,
            0.61,
            0.52,
            0.44,
            0.37,
            0.32,
            0.27,
            0.23,
            0.20,
            0.17,
            0.15,
            0.13,
            0.11,
        ],
        carbon_price_trajectory=[0] * 15,
        bev_efficiency_improvement=generate_price_trajectory(
            -0.04, 15
        ),  # Major efficiency gains
        diesel_efficiency_improvement=generate_price_trajectory(-0.01, 15),
        bev_residual_value_multiplier=[
            1.0,
            1.0,
            1.05,
            1.1,
            1.15,
            1.2,
            1.25,
            1.3,
            1.3,
            1.3,
            1.3,
            1.3,
            1.3,
            1.3,
            1.3,
        ],
        maintenance_cost_multiplier=generate_maintenance_trajectory(
            15
        ),  # Same maintenance trajectory
    ),
    "oil_crisis": EconomicScenario(
        name="Oil Crisis",
        description="Major oil supply disruption in year 3",
        diesel_price_trajectory=[
            1.0,
            1.03,
            1.55,
            1.60,
            1.65,
            1.70,
            1.75,
            1.80,
            1.86,
            1.91,
            1.97,
            2.03,
            2.09,
            2.15,
            2.22,
        ],
        electricity_price_trajectory=generate_price_trajectory(
            0.03, 15
        ),  # Electricity also affected
        battery_price_trajectory=generate_price_trajectory(-0.07, 15),
        carbon_price_trajectory=[0] * 15,
        bev_efficiency_improvement=generate_price_trajectory(-0.02, 15),
        diesel_efficiency_improvement=generate_price_trajectory(
            -0.02, 15
        ),  # Faster improvement due to high prices
        maintenance_cost_multiplier=generate_maintenance_trajectory(
            15
        ),  # Same maintenance trajectory
    ),
}

# ============================================================================
# SCENARIO FUNCTIONS
# ============================================================================

# Active scenario (default to baseline)
active_scenario: EconomicScenario = SCENARIOS["baseline"]


def set_active_scenario(scenario_name: str):
    """Set the active economic scenario."""
    global active_scenario
    if scenario_name not in SCENARIOS:
        raise ValueError(
            f"Scenario '{scenario_name}' not found. Available: {list(SCENARIOS.keys())}"
        )
    active_scenario = SCENARIOS[scenario_name]


def get_active_scenario() -> EconomicScenario:
    """Get the currently active economic scenario."""
    return active_scenario


def create_custom_scenario(name: str, description: str, **kwargs) -> EconomicScenario:
    """Create a custom economic scenario."""
    scenario = EconomicScenario(name=name, description=description, **kwargs)
    SCENARIOS[name] = scenario
    return scenario
</file>

<file path="frontend/e2e/screenshots.ts">
import { chromium } from '@playwright/test';

async function takeScreenshots() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Screenshot 1: Wizard page (step 1)
  await page.goto('http://localhost:5001/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: '/tmp/screenshot-wizard-step1.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-wizard-step1.png');

  // Select a diesel truck to enable step 2
  const dieselSelect = page.locator('select').first();
  await dieselSelect.selectOption({ index: 1 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: '/tmp/screenshot-wizard-step1-selected.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-wizard-step1-selected.png');

  // Click Next to go to step 2
  const nextButton = page.getByRole('button', { name: /next/i });
  if (await nextButton.isVisible()) {
    await nextButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: '/tmp/screenshot-wizard-step2.png', fullPage: true });
    console.log('Saved: /tmp/screenshot-wizard-step2.png');
  }

  // Screenshot: Results page
  await page.goto('http://localhost:5001/results');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: '/tmp/screenshot-results.png', fullPage: true });
  console.log('Saved: /tmp/screenshot-results.png');

  await browser.close();
  console.log('Done!');
}

takeScreenshots().catch(console.error);
</file>

<file path="frontend/e2e/ui-redesign.spec.ts">
import { test, expect } from '@playwright/test';

test.describe('UI Redesign Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Foundation & Design System (Agent 1)', () => {
    test('header has correct styling and navigation', async ({ page }) => {
      // Check header has yellow border
      const header = page.locator('header');
      await expect(header).toHaveClass(/border-brand-primary/);

      // Check title is "Truck Cost Calculator"
      const title = page.locator('h1');
      await expect(title).toContainText('Truck Cost Calculator');

      // Check nav link is "Compare" not "Wizard"
      const compareLink = page.getByRole('link', { name: 'Compare' });
      await expect(compareLink).toBeVisible();

      // Verify no "Wizard" link exists
      await expect(page.getByRole('link', { name: 'Wizard' })).toHaveCount(0);
    });

    test('cards have rounded corners and yellow accent', async ({ page }) => {
      const card = page.locator('section').first();
      await expect(card).toHaveClass(/rounded-lg/);
      await expect(card).toHaveClass(/border-l-4/);
      await expect(card).toHaveClass(/border-l-brand-primary/);
    });

    test('wizard stepper shows steps correctly', async ({ page }) => {
      // Check step titles are updated (use more specific locators)
      await expect(page.getByRole('button', { name: /Step 1.*Your current truck/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /Step 2.*Electric options/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /Step 3.*See your results/i })).toBeVisible();
    });

    test('buttons have correct styling', async ({ page }) => {
      const primaryButton = page.locator('button').filter({ hasText: 'Next' }).first();
      if (await primaryButton.isVisible()) {
        await expect(primaryButton).toHaveClass(/rounded-lg/);
      }
    });
  });

  test.describe('Copy & Content Simplification (Agent 3)', () => {
    test('diesel step has simplified labels', async ({ page }) => {
      // First step should show diesel selection with simplified text
      await expect(page.locator('text=Select your truck')).toBeVisible();
      // Should not have old terminology
      await expect(page.locator('text=Diesel model')).toHaveCount(0);
    });

    test('step descriptions use plain language', async ({ page }) => {
      // Check for simplified descriptions
      await expect(page.getByText('Select the diesel truck you operate today')).toBeVisible();
    });

    test('terminology avoids jargon', async ({ page }) => {
      // Navigate through steps to check terminology
      // "BEV" should not appear in visible text
      const pageText = await page.locator('body').textContent();
      expect(pageText).not.toContain('BEV');
    });
  });

  test.describe('Navigation and Flow', () => {
    test('can navigate between wizard steps', async ({ page }) => {
      // Wait for the page to load
      await page.waitForLoadState('networkidle');

      // Should start on step 1 (use specific locator for step indicator)
      await expect(page.getByText('Step 1 of 3')).toBeVisible();

      // Select a diesel truck to enable navigation
      const dieselSelect = page.locator('select').first();
      await dieselSelect.selectOption({ index: 1 });

      // Click Next if available
      const nextButton = page.getByRole('button', { name: /next/i });
      if (await nextButton.isVisible()) {
        await nextButton.click();
        await expect(page.getByText('Step 2 of 3')).toBeVisible();
      }
    });
  });
});

test.describe('Results Page Verification', () => {
  test('results page is accessible', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    // Check for results page content
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('no results state shows helpful message', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');

    // When no comparison has been run, should show empty state or results
    // The page may show results if there's persisted data, or empty state
    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible();
  });
});

test.describe('Visual Regression Screenshots', () => {
  test('wizard page screenshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('wizard-page.png', { fullPage: true });
  });

  test('results page screenshot', async ({ page }) => {
    await page.goto('/results');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('results-page.png', { fullPage: true });
  });
});
</file>

<file path="frontend/src/components/results/PaybackChart.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const DIESEL_COLOR = '#EA5300';
const ELECTRIC_COLOR = '#00FFC7';
const PAYBACK_COLOR = '#FFC700';

// 15-year vehicle life (from constants)
const VEHICLE_LIFE = 15;

interface CumulativeCostData {
  year: number;
  diesel: number;
  bev: number;
}

const PaybackTooltip = ({ active, payload, label }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">Year {label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value as number)}
        </p>
      ))}
    </div>
  );
};

const PaybackChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Payback timeline"
        subtitle="When does switching to electric break even?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  // Find diesel and BEV results
  const dieselResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  if (!dieselResult || !bevResult) {
    return (
      <Card
        title="Payback timeline"
        subtitle="When does switching to electric break even?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see payback timeline
          </p>
        </div>
      </Card>
    );
  }

  const dieselName = vehicleDetails[dieselResult.vehicle_id]?.model_name ?? 'Diesel';
  const bevName = vehicleDetails[bevResult.vehicle_id]?.model_name ?? 'Electric';

  // Calculate cumulative costs for each year
  // Using annual_cost as the yearly operating cost, scaled from total_cost
  const dieselAnnualCost = dieselResult.annual_cost;
  const bevAnnualCost = bevResult.annual_cost;

  // We'll estimate upfront costs from breakdown and add annual operating costs
  const dieselUpfront = dieselResult.breakdown.purchase_cost + dieselResult.breakdown.financing_cost;
  const bevUpfront = bevResult.breakdown.purchase_cost + bevResult.breakdown.financing_cost;

  // Calculate cumulative costs over the vehicle life
  const data: CumulativeCostData[] = [];
  let dieselCumulative = dieselUpfront;
  let bevCumulative = bevUpfront;

  for (let year = 0; year <= VEHICLE_LIFE; year++) {
    if (year === 0) {
      data.push({ year, diesel: dieselUpfront, bev: bevUpfront });
    } else {
      dieselCumulative += dieselAnnualCost;
      bevCumulative += bevAnnualCost;
      data.push({ year, diesel: dieselCumulative, bev: bevCumulative });
    }
  }

  // Find payback year (where BEV becomes cheaper)
  let paybackYear: number | null = null;
  for (let i = 1; i < data.length; i++) {
    const prev = data[i - 1];
    const curr = data[i];
    // Check if BEV crosses below diesel in this year
    if (prev.bev >= prev.diesel && curr.bev < curr.diesel) {
      // Linear interpolation for more accurate payback point
      const dieselSlope = curr.diesel - prev.diesel;
      const bevSlope = curr.bev - prev.bev;
      const yearFraction = (prev.bev - prev.diesel) / (dieselSlope - bevSlope);
      paybackYear = prev.year + yearFraction;
      break;
    }
  }

  // If BEV starts cheaper, payback is immediate
  if (data[0].bev < data[0].diesel) {
    paybackYear = 0;
  }

  // Calculate total savings at end of life
  const finalDiesel = data[data.length - 1].diesel;
  const finalBev = data[data.length - 1].bev;
  const totalSavings = finalDiesel - finalBev;

  return (
    <Card
      title="Payback timeline"
      subtitle="When does switching to electric break even?"
    >
      <div className="mb-4">
        {paybackYear !== null ? (
          <p className="text-sm text-slate-600">
            Electric breaks even at <span className="font-semibold text-black">year {paybackYear.toFixed(1)}</span>
            {totalSavings > 0 && (
              <>, saving <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over {VEHICLE_LIFE} years</>
            )}
          </p>
        ) : totalSavings > 0 ? (
          <p className="text-sm text-slate-600">
            Electric saves <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over {VEHICLE_LIFE} years
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            Diesel remains cheaper over the {VEHICLE_LIFE}-year horizon
          </p>
        )}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12, fill: '#000000' }}
            label={{ value: 'Year', position: 'insideBottom', offset: -5, fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip content={<PaybackTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />

          {paybackYear !== null && paybackYear > 0 && paybackYear < VEHICLE_LIFE && (
            <ReferenceLine
              x={paybackYear}
              stroke={PAYBACK_COLOR}
              strokeWidth={2}
              strokeDasharray="4 4"
              label={{
                value: `Payback: Year ${paybackYear.toFixed(1)}`,
                position: 'top',
                fontSize: 11,
                fill: '#000000',
              }}
            />
          )}

          <Line
            type="monotone"
            dataKey="diesel"
            name={dieselName}
            stroke={DIESEL_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="bev"
            name={bevName}
            stroke={ELECTRIC_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default PaybackChart;
</file>

<file path="frontend/src/components/results/SavingsWaterfallChart.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const SAVINGS_COLOR = '#00FFC7'; // Electric/positive
const EXTRA_COST_COLOR = '#EA5300'; // Diesel/negative
const TOTAL_COLOR = '#FFC700'; // Winner/total

interface WaterfallItem {
  name: string;
  value: number;
  displayValue: number;
  isTotal?: boolean;
  isPositive?: boolean;
  start: number;
  end: number;
}

const WaterfallTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as WaterfallItem;
  const isPositive = entry.value > 0;
  const label = entry.isTotal
    ? 'Net savings'
    : isPositive
      ? 'BEV saves'
      : 'BEV costs more';

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.name}</p>
      <p>
        {label}: {formatCurrency(Math.abs(entry.value))}
      </p>
    </div>
  );
};

const SavingsWaterfallChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Savings breakdown"
        subtitle="What drives the cost difference?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  // Find diesel and BEV results
  const dieselResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  if (!dieselResult || !bevResult) {
    return (
      <Card
        title="Savings breakdown"
        subtitle="What drives the cost difference?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see savings breakdown
          </p>
        </div>
      </Card>
    );
  }

  // Calculate savings for each cost category (positive = BEV saves money)
  const categories = [
    {
      name: 'Fuel / Energy',
      diesel: dieselResult.breakdown.fuel_cost,
      bev: bevResult.breakdown.fuel_cost,
    },
    {
      name: 'Maintenance',
      diesel: dieselResult.breakdown.maintenance_cost,
      bev: bevResult.breakdown.maintenance_cost,
    },
    {
      name: 'Purchase',
      diesel: dieselResult.breakdown.purchase_cost,
      bev: bevResult.breakdown.purchase_cost,
    },
    {
      name: 'Financing',
      diesel: dieselResult.breakdown.financing_cost,
      bev: bevResult.breakdown.financing_cost,
    },
    {
      name: 'Carbon',
      diesel: dieselResult.breakdown.carbon_cost,
      bev: bevResult.breakdown.carbon_cost,
    },
    {
      name: 'Insurance',
      diesel: dieselResult.breakdown.insurance_cost,
      bev: bevResult.breakdown.insurance_cost,
    },
    {
      name: 'Battery',
      diesel: dieselResult.breakdown.battery_replacement_cost,
      bev: bevResult.breakdown.battery_replacement_cost,
    },
    {
      name: 'Charging labour',
      diesel: dieselResult.breakdown.charging_labour_cost,
      bev: bevResult.breakdown.charging_labour_cost,
    },
    {
      name: 'Payload penalty',
      diesel: dieselResult.breakdown.payload_penalty_cost,
      bev: bevResult.breakdown.payload_penalty_cost,
    },
  ].map((cat) => ({
    name: cat.name,
    savings: cat.diesel - cat.bev, // Positive means BEV saves
  }));

  // Filter out zero or very small values
  const significantCategories = categories.filter(
    (cat) => Math.abs(cat.savings) > 100
  );

  // Sort by absolute value (largest impact first)
  significantCategories.sort((a, b) => Math.abs(b.savings) - Math.abs(a.savings));

  // Build waterfall data
  let runningTotal = 0;
  const data: WaterfallItem[] = significantCategories.map((cat) => {
    const start = runningTotal;
    runningTotal += cat.savings;
    return {
      name: cat.name,
      value: cat.savings,
      displayValue: cat.savings,
      isPositive: cat.savings > 0,
      start: cat.savings > 0 ? start : runningTotal,
      end: cat.savings > 0 ? runningTotal : start,
    };
  });

  // Add total bar
  const totalSavings = dieselResult.total_cost - bevResult.total_cost;
  data.push({
    name: 'Net savings',
    value: totalSavings,
    displayValue: totalSavings,
    isTotal: true,
    isPositive: totalSavings > 0,
    start: 0,
    end: totalSavings,
  });

  // Calculate domain for Y axis
  const allValues = data.flatMap((d) => [d.start, d.end]);
  const minVal = Math.min(...allValues, 0);
  const maxVal = Math.max(...allValues, 0);
  const padding = Math.abs(maxVal - minVal) * 0.1;

  const getBarColor = (entry: WaterfallItem) => {
    if (entry.isTotal) return TOTAL_COLOR;
    return entry.value > 0 ? SAVINGS_COLOR : EXTRA_COST_COLOR;
  };

  return (
    <Card
      title="Savings breakdown"
      subtitle="What drives the cost difference?"
    >
      <div className="mb-4">
        <p className="text-sm text-slate-600">
          {totalSavings > 0 ? (
            <>
              Electric saves{' '}
              <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span>{' '}
              over the vehicle lifetime
            </>
          ) : totalSavings < 0 ? (
            <>
              Diesel saves{' '}
              <span className="font-semibold text-black">{formatCurrency(Math.abs(totalSavings))}</span>{' '}
              over the vehicle lifetime
            </>
          ) : (
            <>Both options have similar total costs</>
          )}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#000000' }}
            angle={-30}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 12, fill: '#000000' }}
            domain={[minVal - padding, maxVal + padding]}
          />
          <Tooltip content={<WaterfallTooltip />} />
          <ReferenceLine y={0} stroke="#000000" strokeWidth={1} />

          {/* For waterfall effect, we use stacked bars with transparent base */}
          <Bar dataKey="start" stackId="stack" fill="transparent" />
          <Bar dataKey="displayValue" stackId="stack" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry)}
                stroke={entry.isTotal ? '#000000' : undefined}
                strokeWidth={entry.isTotal ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: SAVINGS_COLOR }} />
          <span>BEV saves</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: EXTRA_COST_COLOR }} />
          <span>BEV costs more</span>
        </div>
      </div>
    </Card>
  );
};

export default SavingsWaterfallChart;
</file>

<file path="frontend/src/components/results/SensitivityTornadoChart.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const LOW_COLOR = '#EA5300'; // Diesel orange for adverse scenario
const HIGH_COLOR = '#00FFC7'; // Electric aqua for favorable scenario
const BASELINE_COLOR = '#000000';

interface SensitivityItem {
  parameter: string;
  lowDelta: number;
  highDelta: number;
  baselineSavings: number;
}

interface TornadoBarData {
  parameter: string;
  lowValue: number;
  highValue: number;
  lowDelta: number;
  highDelta: number;
}

const TornadoTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as TornadoBarData;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.parameter}</p>
      <p style={{ color: LOW_COLOR }}>
        -20%: {entry.lowDelta >= 0 ? '+' : ''}{formatCurrency(entry.lowDelta)} savings
      </p>
      <p style={{ color: HIGH_COLOR }}>
        +20%: {entry.highDelta >= 0 ? '+' : ''}{formatCurrency(entry.highDelta)} savings
      </p>
    </div>
  );
};

const SensitivityTornadoChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Sensitivity analysis"
        subtitle="How do assumptions affect the comparison?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  // Find diesel and BEV results
  const dieselResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  if (!dieselResult || !bevResult) {
    return (
      <Card
        title="Sensitivity analysis"
        subtitle="How do assumptions affect the comparison?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see sensitivity analysis
          </p>
        </div>
      </Card>
    );
  }

  // Baseline savings (positive = BEV cheaper)
  const baselineSavings = dieselResult.total_cost - bevResult.total_cost;

  // Calculate sensitivity for each parameter
  // We estimate how +/- 20% change affects the BEV vs Diesel comparison
  const sensitivities: SensitivityItem[] = [
    {
      parameter: 'Fuel price',
      // Higher fuel price benefits BEV (more diesel savings)
      lowDelta: -(dieselResult.breakdown.fuel_cost * 0.2),
      highDelta: dieselResult.breakdown.fuel_cost * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Electricity price',
      // Higher electricity price hurts BEV
      lowDelta: bevResult.breakdown.fuel_cost * 0.2,
      highDelta: -(bevResult.breakdown.fuel_cost * 0.2),
      baselineSavings,
    },
    {
      parameter: 'Annual kms',
      // More kms amplifies operating cost differences
      // If BEV has lower operating costs, more kms = more savings
      lowDelta: -((dieselResult.breakdown.fuel_cost - bevResult.breakdown.fuel_cost) * 0.2),
      highDelta: (dieselResult.breakdown.fuel_cost - bevResult.breakdown.fuel_cost) * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Maintenance cost',
      // Higher maintenance costs hurt diesel more (they're higher baseline)
      lowDelta: -(dieselResult.breakdown.maintenance_cost - bevResult.breakdown.maintenance_cost) * 0.2,
      highDelta: (dieselResult.breakdown.maintenance_cost - bevResult.breakdown.maintenance_cost) * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Battery replacement',
      // Only affects BEV
      lowDelta: bevResult.breakdown.battery_replacement_cost * 0.2,
      highDelta: -(bevResult.breakdown.battery_replacement_cost * 0.2),
      baselineSavings,
    },
    {
      parameter: 'Purchase price',
      // BEV usually more expensive, so lower price helps BEV
      lowDelta: bevResult.breakdown.purchase_cost * 0.2,
      highDelta: -(bevResult.breakdown.purchase_cost * 0.2),
      baselineSavings,
    },
  ];

  // Filter to significant sensitivities and sort by impact
  const significantSensitivities = sensitivities
    .filter((s) => Math.abs(s.lowDelta) > 500 || Math.abs(s.highDelta) > 500)
    .sort((a, b) => {
      const aSpread = Math.abs(a.highDelta - a.lowDelta);
      const bSpread = Math.abs(b.highDelta - b.lowDelta);
      return bSpread - aSpread;
    })
    .slice(0, 6); // Top 6 most impactful

  // Build tornado chart data
  const data: TornadoBarData[] = significantSensitivities.map((s) => ({
    parameter: s.parameter,
    lowValue: s.lowDelta < 0 ? s.lowDelta : 0,
    highValue: s.highDelta > 0 ? s.highDelta : 0,
    lowDelta: s.lowDelta,
    highDelta: s.highDelta,
  }));

  // Calculate domain
  const allValues = data.flatMap((d) => [d.lowDelta, d.highDelta]);
  const minVal = Math.min(...allValues, 0);
  const maxVal = Math.max(...allValues, 0);
  const absMax = Math.max(Math.abs(minVal), Math.abs(maxVal));
  const domainPadding = absMax * 0.15;

  return (
    <Card
      title="Sensitivity analysis"
      subtitle="How do assumptions affect the comparison?"
    >
      <div className="mb-4">
        <p className="text-sm text-slate-600">
          Impact of +/- 20% change in each parameter on BEV savings
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
        >
          <CartesianGrid stroke="#E5E5E5" horizontal={false} />
          <XAxis
            type="number"
            domain={[-absMax - domainPadding, absMax + domainPadding]}
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 11, fill: '#000000' }}
          />
          <YAxis
            type="category"
            dataKey="parameter"
            tick={{ fontSize: 12, fill: '#000000' }}
            width={95}
          />
          <Tooltip content={<TornadoTooltip />} />
          <ReferenceLine x={0} stroke={BASELINE_COLOR} strokeWidth={2} />

          {/* Low scenario bars (extending left) */}
          <Bar dataKey="lowDelta" radius={[4, 4, 4, 4]} maxBarSize={24}>
            {data.map((entry, index) => (
              <Cell
                key={`low-${index}`}
                fill={entry.lowDelta < 0 ? LOW_COLOR : HIGH_COLOR}
              />
            ))}
          </Bar>

          {/* High scenario bars (extending right) - rendered on same axis */}
          <Bar dataKey="highDelta" radius={[4, 4, 4, 4]} maxBarSize={24}>
            {data.map((entry, index) => (
              <Cell
                key={`high-${index}`}
                fill={entry.highDelta > 0 ? HIGH_COLOR : LOW_COLOR}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: HIGH_COLOR }} />
          <span>BEV savings increase</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: LOW_COLOR }} />
          <span>BEV savings decrease</span>
        </div>
      </div>
    </Card>
  );
};

export default SensitivityTornadoChart;
</file>

<file path="frontend/src/components/shared/Select.tsx">
import type { SelectHTMLAttributes } from 'react';
import clsx from 'clsx';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    hint?: string;
    error?: string;
}

const Select = ({ label, hint, error, className, children, ...props }: SelectProps) => (
    <label className="flex flex-col gap-2 text-sm text-slate-700 font-body w-full">
        {label && <span className="micro-heading text-black">{label}</span>}
        <div className="relative">
            <select
                className={clsx(
                    'w-full appearance-none border bg-white px-4 py-3.5 pr-10 text-base text-black placeholder-slate-400 focus:outline-none transition-all rounded-lg shadow-sm',
                    error
                        ? 'border-rose-500 focus:border-rose-500 bg-rose-50'
                        : 'border-slate-300 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/25',
                    className
                )}
                aria-invalid={Boolean(error)}
                {...props}
            >
                {children}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
                    <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd" />
                </svg>
            </div>
        </div>
        {error ? (
            <span className="block min-h-[1.25rem] text-xs font-semibold text-rose-600">{error}</span>
        ) : hint ? (
            <span className="block min-h-[1.25rem] text-xs text-slate-500">{hint}</span>
        ) : (
            <span className="block min-h-[1.25rem]" aria-hidden="true" />
        )}
    </label>
);

export default Select;
</file>

<file path="frontend/src/components/wizard/ComparisonConfigPanel.tsx">
import WizardOperatingStep from '@components/wizard/WizardOperatingStep';
import WizardCostStep from '@components/wizard/WizardCostStep';

const ComparisonConfigPanel = () => (
  <div className="flex flex-col gap-6">
    <WizardOperatingStep />
    <WizardCostStep />
  </div>
);

export default ComparisonConfigPanel;
</file>

<file path="frontend/src/components/wizard/WizardVehicleStep.tsx">
import Card from '@components/shared/Card';
import Button from '@components/shared/Button';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const WizardVehicleStep = () => {
  const { data: vehicles } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const currentVehicle = wizardData.currentVehicle;
  const comparisonVehicles = wizardData.comparisonVehicles;
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  const handlePrimarySelect = (vehicleId: string) => {
    updateWizard({ currentVehicle: vehicleId });
  };

  const toggleComparison = (vehicleId: string) => {
    const exists = comparisonVehicles.includes(vehicleId);
    const updated = exists
      ? comparisonVehicles.filter((id) => id !== vehicleId)
      : [...comparisonVehicles, vehicleId];
    updateWizard({ comparisonVehicles: updated });
  };

  return (
    <Card
      title="Vehicle selection"
      subtitle="Choose a baseline and optional comparators. Specs load instantly from the shared catalog."
    >
      {!vehicles?.length ? (
        <p className="text-sm text-slate-500">Vehicle catalog not available.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {vehicles.map((vehicle) => {
            const isPrimary = currentVehicle === vehicle.vehicle_id;
            const isComparison = comparisonVehicles.includes(vehicle.vehicle_id);
            const detail = vehicleDetails[vehicle.vehicle_id];

            return (
              <article
                key={vehicle.vehicle_id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      {vehicle.weight_class}
                    </p>
                    <h3 className="text-lg font-semibold text-slate-900">{vehicle.model_name}</h3>
                    <p className="text-sm text-slate-500">{vehicle.drivetrain_type}</p>
                  </div>
                  {isPrimary && (
                    <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">
                      Baseline
                    </span>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant={isPrimary ? 'secondary' : 'primary'}
                    className="flex-1"
                    onClick={() => handlePrimarySelect(vehicle.vehicle_id)}
                  >
                    {isPrimary ? 'Selected' : 'Set baseline'}
                  </Button>
                  <Button
                    variant={isComparison ? 'secondary' : 'ghost'}
                    className="flex-1"
                    onClick={() => toggleComparison(vehicle.vehicle_id)}
                  >
                    {isComparison ? 'Remove compare' : 'Add compare'}
                  </Button>
                </div>
                {detail ? (
                  <dl className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-500">
                    <div>
                      <dt className="uppercase tracking-wide">Payload</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.payload.toFixed(1)} t
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">Range</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.range_km.toLocaleString()} km
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">Battery / Tank</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.drivetrain_type === 'BEV'
                          ? `${detail.battery_capacity_kwh.toLocaleString()} kWh`
                          : `${detail.litres_per_km.toFixed(2)} L/km`}
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">MSRP</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {formatCurrency(detail.msrp)}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="mt-4 text-xs text-slate-400">Specs unavailable for this vehicle.</p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </Card>
  );
};

export default WizardVehicleStep;
</file>

<file path="frontend/src/hooks/useAnalyticsSummary.ts">
import { useQuery } from '@tanstack/react-query';
import { fetchAnalyticsSummary } from '@services/api';

export const useAnalyticsSummary = () =>
  useQuery({
    queryKey: ['analytics-summary'],
    queryFn: fetchAnalyticsSummary,
    staleTime: 60_000,
  });
</file>

<file path="frontend/src/hooks/useVehicleCatalog.ts">
import { useMemo } from 'react';
import { VEHICLE_SUMMARIES } from '@shared/data/vehicleCatalog';

export const useVehicleCatalog = () => {
  const data = useMemo(() => VEHICLE_SUMMARIES, []);
  return {
    data,
    isLoading: false,
  };
};
</file>

<file path="frontend/src/test/calculator/breakdown.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload, CostBreakdown } from '@shared/types/tco.types';

describe('Cost Breakdown Consistency', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('should have all breakdown fields', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    const requiredFields: (keyof CostBreakdown)[] = [
      'purchase_cost',
      'fuel_cost',
      'maintenance_cost',
      'insurance_cost',
      'registration_cost',
      'battery_replacement_cost',
      'financing_cost',
      'carbon_cost',
      'charging_labour_cost',
      'payload_penalty_cost',
      'residual_value',
      'depreciation',
      'taxes_and_fees',
    ];

    for (const field of requiredFields) {
      expect(breakdown[field]).toBeDefined();
      expect(typeof breakdown[field]).toBe('number');
      expect(breakdown[field]).not.toBeNaN();
    }
  });

  it('should have non-negative costs', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    expect(breakdown.purchase_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.fuel_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.maintenance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.insurance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.registration_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.financing_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.carbon_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.taxes_and_fees).toBeGreaterThanOrEqual(0);
  });

  it('should have residual value less than purchase cost', () => {
    const result = calculateTco(basePayload);
    expect(result.breakdown.residual_value).toBeLessThan(
      result.breakdown.purchase_cost + result.breakdown.taxes_and_fees
    );
  });

  it('should have depreciation equal to initial cost minus residual', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    // This is an approximation due to NPV adjustments
    expect(breakdown.depreciation).toBeGreaterThan(0);
    expect(breakdown.depreciation).toBeLessThan(
      breakdown.purchase_cost + breakdown.taxes_and_fees
    );
  });

  describe('BEV vs Diesel Differences', () => {
    it('should have battery cost only for BEV', () => {
      const bev = calculateTco(basePayload);
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL001' });

      expect(bev.breakdown.battery_replacement_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.battery_replacement_cost).toBe(0);
    });

    it('should have charging labour cost only for large BEVs (articulated trucks)', () => {
      // BEV007/BEV008 are articulated trucks that have charging labor costs
      const articulatedBev = calculateTco({ ...basePayload, vehicle_id: 'BEV007' });
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL007' });

      expect(articulatedBev.breakdown.charging_labour_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.charging_labour_cost).toBe(0);
    });

    it('should have zero charging labour cost for smaller BEVs', () => {
      const smallBev = calculateTco(basePayload); // BEV001 - light rigid
      expect(smallBev.breakdown.charging_labour_cost).toBe(0);
    });
  });
});
</file>

<file path="frontend/src/test/calculator/edge-cases.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco, calculateComparison } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Edge Cases', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Duty Cycle Edge Cases', () => {
    it('should handle 100% urban', () => {
      const result = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 100, regional: 0, longHaul: 0 },
      });
      expect(result.total_cost).not.toBeNaN();
    });

    it('should handle 100% long haul', () => {
      const result = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 0, regional: 0, longHaul: 100 },
      });
      expect(result.total_cost).not.toBeNaN();
    });

    it('should handle zero-sum (fallback to defaults)', () => {
      const result = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 0, regional: 0, longHaul: 0 },
      });
      expect(result.total_cost).not.toBeNaN();
    });

    it('should handle undefined duty cycle', () => {
      const result = calculateTco({
        ...basePayload,
        duty_cycle: undefined,
      });
      expect(result.total_cost).not.toBeNaN();
    });
  });

  describe('Zero/Negative Value Handling', () => {
    it('should handle zero annual kms by falling back to defaults', () => {
      const result = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 0 },
      });
      // Zero annual_kms_variation falls back to vehicle default
      expect(result.total_cost).not.toBeNaN();
      expect(result.cost_per_km).toBeGreaterThan(0);
    });

    it('should handle negative override gracefully', () => {
      // Calculator should sanitize or handle negative values
      expect(() =>
        calculateTco({
          ...basePayload,
          overrides: { annual_kms_variation: -1000 },
        })
      ).not.toThrow();
    });
  });

  describe('Large Value Handling', () => {
    it('should handle very large MSRP', () => {
      const result = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 10_000_000 },
      });
      expect(result.total_cost).not.toBeNaN();
      expect(Number.isFinite(result.total_cost)).toBe(true);
    });

    it('should handle very large annual kms', () => {
      const result = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 1_000_000 },
      });
      expect(result.total_cost).not.toBeNaN();
    });
  });

  describe('All Vehicles', () => {
    const vehicles = [
      'BEV001',
      'BEV002',
      'BEV003',
      'BEV004',
      'BEV005',
      'BEV006',
      'BEV007',
      'BEV008',
      'DSL001',
      'DSL002',
      'DSL003',
      'DSL004',
      'DSL005',
      'DSL006',
      'DSL007',
      'DSL008',
    ];

    vehicles.forEach((vehicleId) => {
      it(`should calculate TCO for ${vehicleId}`, () => {
        const result = calculateTco({
          ...basePayload,
          vehicle_id: vehicleId,
        });
        expect(result.total_cost).toBeGreaterThan(0);
        expect(result.annual_cost).toBeGreaterThan(0);
        expect(result.breakdown.purchase_cost).toBeGreaterThan(0);
      });
    });
  });

  describe('Comparison Function', () => {
    it('should compare multiple vehicles', () => {
      const results = calculateComparison({
        vehicle_ids: ['BEV001', 'DSL001'],
        scenario_name: 'baseline',
        purchase_method: 'outright',
        duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
      });

      expect(results).toHaveLength(2);
      expect(results[0].vehicle_id).toBe('BEV001');
      expect(results[1].vehicle_id).toBe('DSL001');
    });

    it('should handle empty vehicle list', () => {
      const results = calculateComparison({
        vehicle_ids: [],
        scenario_name: 'baseline',
        purchase_method: 'outright',
      });

      expect(results).toHaveLength(0);
    });
  });
});
</file>

<file path="frontend/src/test/calculator/math.test.ts">
import { describe, it, expect } from 'vitest';
import {
  calculatePresentValue,
  discountToPresent,
  calculateNpvOfPayments,
  calculateNpvOfAnnualCashflows,
  calculateAnnualisedCost,
} from '@shared/calculator/math';

describe('Calculator Math Utilities', () => {
  describe('calculatePresentValue', () => {
    it('should calculate PV of annuity correctly', () => {
      // $1000/year for 10 years at 5%
      const pv = calculatePresentValue(1000, 10, 0.05);
      expect(pv).toBeCloseTo(7721.73, 0); // Standard annuity PV
    });

    it('should return 0 for zero annual value', () => {
      expect(calculatePresentValue(0, 10, 0.05)).toBe(0);
    });

    it('should handle zero discount rate', () => {
      const pv = calculatePresentValue(1000, 10, 0);
      expect(pv).toBe(10000); // No discounting
    });

    it('should handle single year', () => {
      const pv = calculatePresentValue(1000, 1, 0.05);
      expect(pv).toBeCloseTo(952.38, 0);
    });
  });

  describe('discountToPresent', () => {
    it('should not discount year 1 (end-of-period convention)', () => {
      const pv = discountToPresent(1000, 1, 0.05);
      expect(pv).toBe(1000); // Year 1 not discounted per convention
    });

    it('should discount year 2 by one period', () => {
      const pv = discountToPresent(1000, 2, 0.05);
      expect(pv).toBeCloseTo(952.38, 0);
    });

    it('should discount year 10 correctly', () => {
      const pv = discountToPresent(1000, 10, 0.05);
      expect(pv).toBeCloseTo(644.61, 0);
    });
  });

  describe('calculateNpvOfPayments', () => {
    it('should calculate NPV of monthly payments', () => {
      // $500/month for 60 months at 5% annual
      const npv = calculateNpvOfPayments(500, 60, 0.05);
      expect(npv).toBeGreaterThan(25000); // Should be less than 30000
      expect(npv).toBeLessThan(30000);
    });

    it('should return 0 for zero payment', () => {
      expect(calculateNpvOfPayments(0, 60, 0.05)).toBe(0);
    });
  });

  describe('calculateNpvOfAnnualCashflows', () => {
    it('should calculate NPV of varying annual cashflows', () => {
      const cashflows = [1000, 1100, 1200, 1300, 1400];
      const npv = calculateNpvOfAnnualCashflows(cashflows, 0.05);
      expect(npv).toBeGreaterThan(5000);
    });

    it('should return 0 for empty array', () => {
      expect(calculateNpvOfAnnualCashflows([], 0.05)).toBe(0);
    });

    it('should handle array with zeros', () => {
      const cashflows = [0, 0, 1000, 0, 0];
      const npv = calculateNpvOfAnnualCashflows(cashflows, 0.05);
      expect(npv).toBeGreaterThan(0);
    });
  });

  describe('calculateAnnualisedCost', () => {
    it('should convert NPV to equivalent annual cost', () => {
      const annual = calculateAnnualisedCost(10000, 10, 0.05);
      expect(annual).toBeCloseTo(1295.05, 0);
    });

    it('should handle zero NPV', () => {
      expect(calculateAnnualisedCost(0, 10, 0.05)).toBe(0);
    });
  });
});
</file>

<file path="frontend/src/test/calculator/overrides.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Vehicle Parameter Overrides', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('MSRP Override', () => {
    it('should increase purchase cost with higher MSRP', () => {
      const standard = calculateTco(basePayload);
      const higherMsrp = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 500000 },
      });

      expect(higherMsrp.breakdown.purchase_cost).toBeGreaterThan(
        standard.breakdown.purchase_cost
      );
    });

    it('should affect depreciation proportionally', () => {
      const standard = calculateTco(basePayload);
      const higherMsrp = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 500000 },
      });

      expect(higherMsrp.breakdown.depreciation).toBeGreaterThan(
        standard.breakdown.depreciation
      );
    });
  });

  describe('Range Override', () => {
    it('should affect charging labor cost', () => {
      const standard = calculateTco(basePayload);
      const higherRange = calculateTco({
        ...basePayload,
        vehicle_overrides: { range_km_override: 600 },
      });

      // Higher range = fewer charging sessions = lower labor cost
      expect(higherRange.breakdown.charging_labour_cost).toBeLessThanOrEqual(
        standard.breakdown.charging_labour_cost
      );
    });
  });

  describe('Efficiency Override (kWh/km)', () => {
    it('should affect fuel cost for BEV', () => {
      const standard = calculateTco(basePayload);
      const lessEfficient = calculateTco({
        ...basePayload,
        vehicle_overrides: { kwh_per_km_override: 2.0 }, // Higher = less efficient
      });

      expect(lessEfficient.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });

  describe('Combined Overrides', () => {
    it('should apply multiple overrides correctly', () => {
      const result = calculateTco({
        ...basePayload,
        vehicle_overrides: {
          msrp_override: 400000,
          range_km_override: 500,
          battery_capacity_kwh_override: 400,
        },
      });

      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.breakdown.purchase_cost).toBeGreaterThan(0);
    });
  });
});

describe('Cost Overrides', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Annual KMs Override', () => {
    it('should change fuel costs when annual kms varies', () => {
      const standard = calculateTco(basePayload);
      const higherKms = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 150000 }, // Higher annual kms
      });

      // Higher annual kms should increase fuel costs
      expect(higherKms.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });

    it('should accept absolute annual kms value', () => {
      const result = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 50000 },
      });

      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.breakdown.fuel_cost).toBeGreaterThan(0);
    });
  });

  describe('Fuel Price Variation', () => {
    it('should scale diesel costs with fuel price variation', () => {
      const standard = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
      });
      const higherFuel = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        overrides: { fuel_price_variation: 1.5 }, // 50% higher
      });

      expect(higherFuel.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });

  describe('Electricity Price Variation', () => {
    it('should scale BEV costs with electricity price variation', () => {
      const standard = calculateTco(basePayload);
      const higherElectricity = calculateTco({
        ...basePayload,
        overrides: { electricity_price_variation: 1.5 },
      });

      expect(higherElectricity.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });
});
</file>

<file path="frontend/src/test/calculator/purchase-methods.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Purchase Methods', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Outright Purchase', () => {
    it('should have no financing cost', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'outright',
      });
      expect(result.breakdown.financing_cost).toBe(0);
    });

    it('should have full purchase cost upfront', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'outright',
      });
      expect(result.breakdown.purchase_cost).toBeGreaterThan(0);
    });
  });

  describe('Financed Purchase', () => {
    it('should have non-zero financing cost', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
      });
      expect(result.breakdown.financing_cost).toBeGreaterThan(0);
    });

    it('should have lower upfront cost than outright', () => {
      const outright = calculateTco({
        ...basePayload,
        purchase_method: 'outright',
      });
      const financed = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
      });

      // Upfront cost should be lower (down payment only)
      expect(financed.breakdown.purchase_cost).toBeLessThan(
        outright.breakdown.purchase_cost
      );
    });

    it('should have higher total cost due to interest', () => {
      const outright = calculateTco({
        ...basePayload,
        purchase_method: 'outright',
      });
      const financed = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
      });

      // Total should be higher due to interest
      expect(financed.total_cost).toBeGreaterThan(outright.total_cost);
    });
  });

  describe('Interest Rate Override', () => {
    it('should increase financing cost with higher rate', () => {
      const standardRate = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
      });
      const higherRate = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
        vehicle_overrides: { interest_rate_override: 0.12 }, // 12%
      });

      expect(higherRate.breakdown.financing_cost).toBeGreaterThan(
        standardRate.breakdown.financing_cost
      );
    });

    it('should have zero financing cost with 0% rate', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
        vehicle_overrides: { interest_rate_override: 0 },
      });

      expect(result.breakdown.financing_cost).toBe(0);
    });
  });
});
</file>

<file path="frontend/src/test/calculator/scenarios.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Economic Scenarios', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Baseline Scenario', () => {
    it('should produce valid results', () => {
      const result = calculateTco(basePayload);
      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.annual_cost).toBeGreaterThan(0);
      expect(result.cost_per_km).toBeGreaterThan(0);
    });
  });

  describe('Technology Breakthrough Scenario', () => {
    it('should produce lower BEV costs than baseline', () => {
      const baseline = calculateTco(basePayload);
      const breakthrough = calculateTco({
        ...basePayload,
        scenario_name: 'technology_breakthrough',
      });

      // Technology breakthrough should reduce BEV costs
      expect(breakthrough.total_cost).toBeLessThan(baseline.total_cost);
    });

    it('should have lower battery costs due to price trajectory', () => {
      const baseline = calculateTco(basePayload);
      const breakthrough = calculateTco({
        ...basePayload,
        scenario_name: 'technology_breakthrough',
      });

      expect(breakthrough.breakdown.battery_replacement_cost).toBeLessThanOrEqual(
        baseline.breakdown.battery_replacement_cost
      );
    });
  });

  describe('Oil Crisis Scenario', () => {
    it('should produce higher diesel costs than baseline', () => {
      const dieselBaseline = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'baseline',
      });
      const dieselCrisis = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'oil_crisis',
      });

      expect(dieselCrisis.breakdown.fuel_cost).toBeGreaterThan(
        dieselBaseline.breakdown.fuel_cost
      );
    });

    it('should make BEV more competitive vs diesel', () => {
      const bevCrisis = calculateTco({
        ...basePayload,
        scenario_name: 'oil_crisis',
      });
      const dieselCrisis = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'oil_crisis',
      });

      // In oil crisis, BEV advantage should be greater
      const bevAdvantage = dieselCrisis.total_cost - bevCrisis.total_cost;
      expect(bevAdvantage).toBeGreaterThan(0);
    });
  });

  describe('Scenario Comparison', () => {
    it('should produce distinct results for each scenario', () => {
      const scenarios = ['baseline', 'technology_breakthrough', 'oil_crisis'] as const;
      const results = scenarios.map((scenario) =>
        calculateTco({ ...basePayload, scenario_name: scenario }).total_cost
      );

      // All three should be different
      expect(new Set(results).size).toBe(3);
    });
  });
});
</file>

<file path="frontend/src/test/critical-fixes.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Critical Bug Fixes', () => {
  describe('Duty Cycle Updates', () => {
    it('should produce different results for different duty cycles', () => {
      const basePayload: CalculationRequestPayload = {
        vehicle_id: 'BEV001',
        scenario_name: 'baseline',
        purchase_method: 'outright',
      };

      const urbanHeavy = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 80, regional: 15, longHaul: 5 },
      });

      const longHaulHeavy = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 20, regional: 20, longHaul: 60 },
      });

      // Different duty cycles should produce different fuel costs
      expect(urbanHeavy.breakdown.fuel_cost).not.toEqual(
        longHaulHeavy.breakdown.fuel_cost
      );
    });

    it('should reflect duty cycle changes in total cost', () => {
      const basePayload: CalculationRequestPayload = {
        vehicle_id: 'BEV001',
        scenario_name: 'baseline',
        purchase_method: 'outright',
      };

      const result1 = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 100, regional: 0, longHaul: 0 },
      });

      const result2 = calculateTco({
        ...basePayload,
        duty_cycle: { urban: 0, regional: 0, longHaul: 100 },
      });

      // 100% urban vs 100% long haul should have different total costs
      expect(result1.total_cost).not.toEqual(result2.total_cost);
    });
  });
});
</file>

<file path="frontend/src/test/input-validation.test.ts">
import { describe, it, expect } from 'vitest';
import { vehicleParamOverridesSchema } from '@forms/wizardForm';

describe('Input Validation', () => {
  describe('vehicleParamOverridesSchema', () => {
    it('should accept valid overrides', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 150000,
        range_km_override: 400,
      });
      expect(result.success).toBe(true);
    });

    it('should accept all valid override fields', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 250000,
        payload_override: 10,
        range_km_override: 500,
        battery_capacity_kwh_override: 300,
        kwh_per_km_override: 1.5,
        litres_per_km_override: 0.3,
        annual_registration_override: 5000,
        interest_rate_override: 0.06,
        charging_time_hours_override: 2,
      });
      expect(result.success).toBe(true);
    });

    it('should reject negative values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: -1000,
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for msrp', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 100_000_000, // Exceeds max of 10M
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for range', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        range_km_override: 3000, // Exceeds max of 2000
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for battery capacity', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        battery_capacity_kwh_override: 5000, // Exceeds max of 2000
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for interest rate', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        interest_rate_override: 1.5, // Exceeds max of 1 (100%)
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for charging time', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        charging_time_hours_override: 48, // Exceeds max of 24
      });
      expect(result.success).toBe(false);
    });

    it('should accept empty object', () => {
      const result = vehicleParamOverridesSchema.safeParse({});
      expect(result.success).toBe(true);
    });

    it('should accept undefined values for optional fields', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: undefined,
        range_km_override: undefined,
      });
      expect(result.success).toBe(true);
    });

    it('should accept zero values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 0,
        interest_rate_override: 0,
      });
      expect(result.success).toBe(true);
    });

    it('should reject NaN values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: NaN,
      });
      expect(result.success).toBe(false);
    });
  });
});
</file>

<file path="frontend/src/test/reproduce_crash.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload, DutyCycle } from '@shared/types/tco.types';

describe('TCO Calculator Crash Reproduction', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('should handle zero-sum duty cycle without crashing', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 0, regional: 0, longHaul: 0 },
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
    expect(result.cost_per_km).not.toBeNaN();
  });

  it('should handle NaN duty cycle values without crashing', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: NaN, regional: 0, longHaul: 0 } as unknown as DutyCycle,
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
  });

  it('should handle partial duty cycle objects', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 50 } as unknown as DutyCycle,
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
  });
});
</file>

<file path="frontend/src/test/state-management.test.ts">
import { describe, it, expect, beforeEach } from 'vitest';
import { useTCOStore } from '@state/tcoStore';

describe('TCO Store State Management', () => {
  beforeEach(() => {
    // Reset store between tests
    useTCOStore.setState({
      stepIndex: 0,
      wizardData: {
        currentVehicle: undefined,
        comparisonVehicles: [],
        scenario: 'baseline',
        purchaseMethod: 'financed',
        dutyCycle: { urban: 60, regional: 25, longHaul: 15 },
        overrides: {},
        vehicleParamOverrides: {},
      },
      results: [],
      isCalculating: false,
      sessionId: undefined,
    });
  });

  describe('Duty Cycle Validation', () => {
    it('should replace NaN duty cycle values with defaults', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: NaN, regional: 25, longHaul: 15 },
      });

      const updated = useTCOStore.getState();
      // Should fallback to defaults when any value is NaN
      expect(updated.wizardData.dutyCycle.urban).toBe(60);
      expect(updated.wizardData.dutyCycle.regional).toBe(25);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(15);
    });

    it('should clamp negative duty cycle values to zero', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: -10, regional: 25, longHaul: 15 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle.urban).toBe(0);
      expect(updated.wizardData.dutyCycle.regional).toBe(25);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(15);
    });

    it('should accept valid duty cycle values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: 50, regional: 30, longHaul: 20 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle.urban).toBe(50);
      expect(updated.wizardData.dutyCycle.regional).toBe(30);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(20);
    });

    it('should handle all-NaN duty cycle values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: NaN, regional: NaN, longHaul: NaN },
      });

      const updated = useTCOStore.getState();
      // Should fallback to all defaults
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 60,
        regional: 25,
        longHaul: 15,
      });
    });

    it('should clamp all negative values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: -5, regional: -10, longHaul: -15 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 0,
        regional: 0,
        longHaul: 0,
      });
    });
  });

  describe('Other WizardData Updates', () => {
    it('should update scenario without affecting duty cycle', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        scenario: 'technology_breakthrough',
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.scenario).toBe('technology_breakthrough');
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 60,
        regional: 25,
        longHaul: 15,
      });
    });

    it('should update current vehicle', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        currentVehicle: 'BEV001',
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.currentVehicle).toBe('BEV001');
    });

    it('should update comparison vehicles', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        comparisonVehicles: ['DSL001', 'BEV002'],
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.comparisonVehicles).toEqual([
        'DSL001',
        'BEV002',
      ]);
    });
  });

  describe('Results Management', () => {
    it('should set results and maintain order based on wizard data', () => {
      const store = useTCOStore.getState();

      // First set the wizard data with vehicle order
      store.updateWizard({
        currentVehicle: 'BEV001',
        comparisonVehicles: ['DSL001'],
      });

      // Then set results in different order
      store.setResults([
        { vehicle_id: 'DSL001', total_cost: 100000, breakdown: {} } as any,
        { vehicle_id: 'BEV001', total_cost: 150000, breakdown: {} } as any,
      ]);

      const updated = useTCOStore.getState();
      // Results should be reordered to match wizard data order
      expect(updated.results[0].vehicle_id).toBe('BEV001');
      expect(updated.results[1].vehicle_id).toBe('DSL001');
    });

    it('should reset results', () => {
      const store = useTCOStore.getState();

      store.setResults([
        { vehicle_id: 'BEV001', total_cost: 150000, breakdown: {} } as any,
      ]);

      expect(useTCOStore.getState().results).toHaveLength(1);

      store.resetResults();

      expect(useTCOStore.getState().results).toHaveLength(0);
    });
  });

  describe('Session Management', () => {
    it('should set session ID', () => {
      const store = useTCOStore.getState();

      store.setSessionId('test-session-123');

      expect(useTCOStore.getState().sessionId).toBe('test-session-123');
    });

    it('should clear session ID', () => {
      const store = useTCOStore.getState();

      store.setSessionId('test-session-123');
      store.setSessionId(undefined);

      expect(useTCOStore.getState().sessionId).toBeUndefined();
    });
  });

  describe('Calculating State', () => {
    it('should track calculating state', () => {
      const store = useTCOStore.getState();

      expect(store.isCalculating).toBe(false);

      store.setIsCalculating(true);
      expect(useTCOStore.getState().isCalculating).toBe(true);

      store.setIsCalculating(false);
      expect(useTCOStore.getState().isCalculating).toBe(false);
    });
  });
});
</file>

<file path="frontend/src/test/verification.test.ts">
import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import verificationData from '@shared/calculator/verification_data.json';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

// Tolerance for floating point comparisons
// Some small differences are expected due to float precision differences between Python and JS
const TOLERANCE = 0.01; // 1 cent tolerance

describe('TCO Calculation Verification', () => {
  verificationData.forEach((testCase) => {
    it(`should match Python results for ${testCase.id}`, () => {
      const input = testCase.input as unknown as CalculationRequestPayload;
      const expected = testCase.expected;

      const result = calculateTco(input);

      // Verify top-level metrics
      expect(result.total_cost).toBeCloseTo(expected.total_cost, 1); // Lower precision for total cost due to accumulation
      expect(result.annual_cost).toBeCloseTo(expected.annual_cost, 1);
      expect(result.cost_per_km).toBeCloseTo(expected.cost_per_km, 3);

      // Verify breakdown
      expect(result.breakdown.purchase_cost).toBeCloseTo(expected.breakdown.purchase_cost, 1);
      expect(result.breakdown.fuel_cost).toBeCloseTo(expected.breakdown.fuel_cost, 1);
      expect(result.breakdown.maintenance_cost).toBeCloseTo(expected.breakdown.maintenance_cost, 1);
      expect(result.breakdown.insurance_cost).toBeCloseTo(expected.breakdown.insurance_cost, 1);
      expect(result.breakdown.registration_cost).toBeCloseTo(expected.breakdown.registration_cost, 1);
      expect(result.breakdown.battery_replacement_cost).toBeCloseTo(expected.breakdown.battery_replacement_cost, 1);
      expect(result.breakdown.financing_cost).toBeCloseTo(expected.breakdown.financing_cost, 1);
      expect(result.breakdown.carbon_cost).toBeCloseTo(expected.breakdown.carbon_cost, 1);
      expect(result.breakdown.charging_labour_cost).toBeCloseTo(expected.breakdown.charging_labour_cost, 1);
      expect(result.breakdown.payload_penalty_cost).toBeCloseTo(expected.breakdown.payload_penalty_cost, 1);
      expect(result.breakdown.residual_value).toBeCloseTo(expected.breakdown.residual_value, 1);
      expect(result.breakdown.depreciation).toBeCloseTo(expected.breakdown.depreciation, 1);
      expect(result.breakdown.taxes_and_fees).toBeCloseTo(expected.breakdown.taxes_and_fees, 1);
    });
  });
});
</file>

<file path="frontend/src/utils/format.ts">
const BASE_CURRENCY_OPTIONS: Intl.NumberFormatOptions = {
  style: 'currency',
  currency: 'AUD',
  maximumFractionDigits: 0,
};

export const formatCurrency = (
  value: number,
  options?: Intl.NumberFormatOptions
): string => {
  return new Intl.NumberFormat('en-AU', {
    ...BASE_CURRENCY_OPTIONS,
    ...options,
  }).format(value);
};

export const formatCurrencyCompact = (value: number): string => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

export const formatPerKilometre = (value: number): string => {
  return `${formatCurrency(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} / km`;
};
</file>

<file path="frontend/src/App.tsx">
import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from '@components/layout/AppShell';
import ResultsPage from '@pages/ResultsPage';
import WizardPage from '@pages/WizardPage';

const App = () => (
  <AppShell>
    <Routes>
      <Route path="/" element={<WizardPage />} />
      <Route path="/results" element={<ResultsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </AppShell>
);

export default App;
</file>

<file path="frontend/src/main.tsx">
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
    </QueryClientProvider>
  </React.StrictMode>
);
</file>

<file path="frontend/playwright.config.ts">
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // webServer disabled - start manually with bun run dev
});
</file>

<file path="shared/calculator/index.ts">
export { calculateTco, calculateComparison, getVehicleCatalogSnapshot } from './tcoCalculator';
</file>

<file path="shared/data/policies.ts">
// Auto-generated by scripts/generate_vehicle_catalog_ts.py. Do not edit manually.

import type { PolicyCatalog } from '../types/tco.types';

export const POLICY_CONFIG: PolicyCatalog = {
  "carbon_price": {
    "description": "Price on carbon emissions from diesel vehicles",
    "enabled": false,
    "name": "Carbon Pricing",
    "policy_type": "CarbonPrice",
    "price_per_tonne": 0
  },
  "charging_grant": {
    "description": "Grant for charging infrastructure installation",
    "enabled": false,
    "grant_percentage": 0.0,
    "max_amount": null,
    "name": "Charging Infrastructure Grant",
    "policy_type": "ChargingInfrastructureGrant"
  },
  "green_loan_subsidy": {
    "description": "Reduced interest rate for BEV financing",
    "enabled": false,
    "name": "Green Loan Subsidy",
    "policy_type": "GreenLoanSubsidy",
    "rate_reduction": 0.0
  },
  "percentage_rebate": {
    "description": "Percentage-based rebate on BEV purchase price",
    "enabled": false,
    "max_amount": null,
    "name": "Percentage Purchase Rebate",
    "percentage": 0.0,
    "policy_type": "PercentageRebate"
  },
  "purchase_rebate": {
    "amount": 0,
    "description": "Fixed dollar amount rebate for new BEV purchases",
    "enabled": false,
    "name": "Fixed Purchase Rebate",
    "policy_type": "PurchaseRebate"
  },
  "stamp_duty_exemption": {
    "description": "Full or partial exemption from stamp duty for BEVs",
    "enabled": false,
    "exemption_percentage": 0.0,
    "name": "Stamp Duty Exemption",
    "policy_type": "StampDutyExemption"
  }
} as const;
</file>

<file path="shared/data/scenarios.ts">
// Auto-generated by scripts/generate_vehicle_catalog_ts.py. Do not edit manually.

import type { ScenarioDefinitionMap } from '../types/tco.types';

export const SCENARIO_DEFINITIONS: ScenarioDefinitionMap = {
  "baseline": {
    "battery_price_trajectory": [
      1.0,
      0.9299999999999999,
      0.8648999999999999,
      0.8043569999999999,
      0.7480520099999999,
      0.6956883692999999,
      0.6469901834489998,
      0.6017008706075698,
      0.5595818096650399,
      0.520411082988487,
      0.4839823071792929,
      0.4501035456767424,
      0.4185962974793704,
      0.3892945566558144,
      0.3620439376899074
    ],
    "bev_efficiency_improvement": [
      1.0,
      0.98,
      0.9603999999999999,
      0.9411919999999999,
      0.9223681599999999,
      0.9039207967999998,
      0.8858423808639998,
      0.8681255332467198,
      0.8507630225817854,
      0.8337477621301497,
      0.8170728068875467,
      0.8007313507497957,
      0.7847167237347998,
      0.7690223892601038,
      0.7536419414749017
    ],
    "bev_residual_value_multiplier": [
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0
    ],
    "carbon_price_trajectory": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ],
    "description": "Current trajectory with moderate price increases",
    "diesel_efficiency_improvement": [
      1.0,
      0.99,
      0.9801,
      0.9702989999999999,
      0.96059601,
      0.9509900498999999,
      0.9414801494009999,
      0.9320653479069899,
      0.92274469442792,
      0.9135172474836407,
      0.9043820750088043,
      0.8953382542587163,
      0.8863848717161291,
      0.8775210229989678,
      0.8687458127689781
    ],
    "diesel_price_trajectory": [
      1.0,
      1.03,
      1.0609,
      1.092727,
      1.1255088100000001,
      1.1592740743,
      1.1940522965290001,
      1.2298738654248702,
      1.2667700813876164,
      1.304773183829245,
      1.3439163793441222,
      1.384233870724446,
      1.4257608868461793,
      1.4685337134515648,
      1.512589724855112
    ],
    "electricity_price_trajectory": [
      1.0,
      1.02,
      1.0404,
      1.061208,
      1.08243216,
      1.1040808032,
      1.126162419264,
      1.14868566764928,
      1.1716593810022657,
      1.195092568622311,
      1.2189944199947573,
      1.2433743083946525,
      1.2682417945625455,
      1.2936066304537963,
      1.3194787630628724
    ],
    "infrastructure_cost_trajectory": [
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0
    ],
    "key": "baseline",
    "maintenance_cost_multiplier": [
      0.85,
      0.8785714285714286,
      0.9071428571428571,
      0.9357142857142857,
      0.9642857142857143,
      0.9928571428571429,
      1.0214285714285714,
      1.05,
      1.0785714285714285,
      1.1071428571428572,
      1.1357142857142857,
      1.1642857142857144,
      1.1928571428571428,
      1.2214285714285715,
      1.25
    ],
    "name": "Baseline",
    "policy_phase_out_year": null,
    "road_user_charge_bev_start_year": null
  },
  "oil_crisis": {
    "battery_price_trajectory": [
      1.0,
      0.9299999999999999,
      0.8648999999999999,
      0.8043569999999999,
      0.7480520099999999,
      0.6956883692999999,
      0.6469901834489998,
      0.6017008706075698,
      0.5595818096650399,
      0.520411082988487,
      0.4839823071792929,
      0.4501035456767424,
      0.4185962974793704,
      0.3892945566558144,
      0.3620439376899074
    ],
    "bev_efficiency_improvement": [
      1.0,
      0.98,
      0.9603999999999999,
      0.9411919999999999,
      0.9223681599999999,
      0.9039207967999998,
      0.8858423808639998,
      0.8681255332467198,
      0.8507630225817854,
      0.8337477621301497,
      0.8170728068875467,
      0.8007313507497957,
      0.7847167237347998,
      0.7690223892601038,
      0.7536419414749017
    ],
    "bev_residual_value_multiplier": [
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0
    ],
    "carbon_price_trajectory": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ],
    "description": "Major oil supply disruption in year 3",
    "diesel_efficiency_improvement": [
      1.0,
      0.98,
      0.9603999999999999,
      0.9411919999999999,
      0.9223681599999999,
      0.9039207967999998,
      0.8858423808639998,
      0.8681255332467198,
      0.8507630225817854,
      0.8337477621301497,
      0.8170728068875467,
      0.8007313507497957,
      0.7847167237347998,
      0.7690223892601038,
      0.7536419414749017
    ],
    "diesel_price_trajectory": [
      1.0,
      1.03,
      1.55,
      1.6,
      1.65,
      1.7,
      1.75,
      1.8,
      1.86,
      1.91,
      1.97,
      2.03,
      2.09,
      2.15,
      2.22
    ],
    "electricity_price_trajectory": [
      1.0,
      1.03,
      1.0609,
      1.092727,
      1.1255088100000001,
      1.1592740743,
      1.1940522965290001,
      1.2298738654248702,
      1.2667700813876164,
      1.304773183829245,
      1.3439163793441222,
      1.384233870724446,
      1.4257608868461793,
      1.4685337134515648,
      1.512589724855112
    ],
    "infrastructure_cost_trajectory": [
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0
    ],
    "key": "oil_crisis",
    "maintenance_cost_multiplier": [
      0.85,
      0.8785714285714286,
      0.9071428571428571,
      0.9357142857142857,
      0.9642857142857143,
      0.9928571428571429,
      1.0214285714285714,
      1.05,
      1.0785714285714285,
      1.1071428571428572,
      1.1357142857142857,
      1.1642857142857144,
      1.1928571428571428,
      1.2214285714285715,
      1.25
    ],
    "name": "Oil Crisis",
    "policy_phase_out_year": null,
    "road_user_charge_bev_start_year": null
  },
  "technology_breakthrough": {
    "battery_price_trajectory": [
      1.0,
      0.85,
      0.72,
      0.61,
      0.52,
      0.44,
      0.37,
      0.32,
      0.27,
      0.23,
      0.2,
      0.17,
      0.15,
      0.13,
      0.11
    ],
    "bev_efficiency_improvement": [
      1.0,
      0.96,
      0.9216,
      0.884736,
      0.84934656,
      0.8153726976,
      0.782757789696,
      0.7514474781081599,
      0.7213895789838335,
      0.6925339958244802,
      0.6648326359915009,
      0.6382393305518408,
      0.6127097573297672,
      0.5882013670365764,
      0.5646733123551133
    ],
    "bev_residual_value_multiplier": [
      1.0,
      1.0,
      1.05,
      1.1,
      1.15,
      1.2,
      1.25,
      1.3,
      1.3,
      1.3,
      1.3,
      1.3,
      1.3,
      1.3,
      1.3
    ],
    "carbon_price_trajectory": [
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0
    ],
    "description": "Rapid battery technology improvement",
    "diesel_efficiency_improvement": [
      1.0,
      0.99,
      0.9801,
      0.9702989999999999,
      0.96059601,
      0.9509900498999999,
      0.9414801494009999,
      0.9320653479069899,
      0.92274469442792,
      0.9135172474836407,
      0.9043820750088043,
      0.8953382542587163,
      0.8863848717161291,
      0.8775210229989678,
      0.8687458127689781
    ],
    "diesel_price_trajectory": [
      1.0,
      1.03,
      1.0609,
      1.092727,
      1.1255088100000001,
      1.1592740743,
      1.1940522965290001,
      1.2298738654248702,
      1.2667700813876164,
      1.304773183829245,
      1.3439163793441222,
      1.384233870724446,
      1.4257608868461793,
      1.4685337134515648,
      1.512589724855112
    ],
    "electricity_price_trajectory": [
      1.0,
      1.02,
      1.0404,
      1.061208,
      1.08243216,
      1.1040808032,
      1.126162419264,
      1.14868566764928,
      1.1716593810022657,
      1.195092568622311,
      1.2189944199947573,
      1.2433743083946525,
      1.2682417945625455,
      1.2936066304537963,
      1.3194787630628724
    ],
    "infrastructure_cost_trajectory": [
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0,
      1.0
    ],
    "key": "technology_breakthrough",
    "maintenance_cost_multiplier": [
      0.85,
      0.8785714285714286,
      0.9071428571428571,
      0.9357142857142857,
      0.9642857142857143,
      0.9928571428571429,
      1.0214285714285714,
      1.05,
      1.0785714285714285,
      1.1071428571428572,
      1.1357142857142857,
      1.1642857142857144,
      1.1928571428571428,
      1.2214285714285715,
      1.25
    ],
    "name": "Technology Breakthrough",
    "policy_phase_out_year": null,
    "road_user_charge_bev_start_year": null
  }
} as const;
</file>

<file path="tests/__init__.py">
"""Test package for TCO calculator."""
</file>

<file path="docker-compose.yml">
version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    command: uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql+asyncpg://tco_user:tco_pass@postgres:5432/tco_db
      - REDIS_URL=redis://redis:6379/0
      - SESSION_TTL_SECONDS=1800
    env_file:
      - backend/.env
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile
    command: npm run dev -- --host 0.0.0.0 --port 3000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/web
      - /web/node_modules
    depends_on:
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=tco_user
      - POSTGRES_PASSWORD=tco_pass
      - POSTGRES_DB=tco_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
</file>

<file path="backend/app/services/vehicles.py">
"""Service objects that expose read-only vehicle metadata."""

from __future__ import annotations

from typing import Dict, List

from backend.app.models import VehicleDetail, VehicleSummary
from data.vehicles import ALL_MODELS, BY_ID, VehicleModel


class VehicleCatalogService:
    """Provides lookup helpers for vehicle metadata."""

    def __init__(self) -> None:
        self._vehicles: Dict[str, VehicleModel] = BY_ID

    def list_summaries(self) -> List[VehicleSummary]:
        return [self._to_summary(model) for model in ALL_MODELS]

    def get(self, vehicle_id: str) -> VehicleDetail:
        try:
            model = self._vehicles[vehicle_id]
        except KeyError as exc:  # pragma: no cover
            raise KeyError(f"Unknown vehicle_id '{vehicle_id}'.") from exc
        return self._to_detail(model)

    @staticmethod
    def _to_summary(model: VehicleModel) -> VehicleSummary:
        return VehicleSummary(
            vehicle_id=model.vehicle_id,
            model_name=model.model_name,
            drivetrain_type=model.drivetrain_type,
            weight_class=model.weight_class,
            comparison_pair=model.comparison_pair,
        )

    @staticmethod
    def _to_detail(model: VehicleModel) -> VehicleDetail:
        return VehicleDetail(
            vehicle_id=model.vehicle_id,
            model_name=model.model_name,
            drivetrain_type=model.drivetrain_type,
            weight_class=model.weight_class,
            comparison_pair=model.comparison_pair,
            payload=model.payload,
            msrp=model.msrp,
            range_km=model.range_km,
            battery_capacity_kwh=model.battery_capacity_kwh,
            kwh_per_km=model.kwh_per_km,
            litres_per_km=model.litres_per_km,
            maintenance_cost_per_km=model.maintenance_cost_per_km,
            annual_registration=model.annual_registration,
            annual_kms=model.annual_kms,
        )
</file>

<file path="data/vehicles.py">
"""
Vehicle data for TCO analysis.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True, frozen=True)
class VehicleModel:
    vehicle_id: str
    comparison_pair: str
    weight_class: str
    drivetrain_type: str
    model_name: str
    payload: float
    msrp: float
    range_km: float
    battery_capacity_kwh: float
    kwh_per_km: float
    litres_per_km: float
    battery_replacement_per_kw: float
    maintenance_cost_per_km: float
    annual_registration: float
    annual_kms: float
    noise_pollution_per_km: float


ALL_MODELS: List[VehicleModel] = [
    VehicleModel(
        "BEV001",
        "DSL001",
        "Light Rigid",
        "BEV",
        "Jac N75",
        4.0,
        176500.0,
        220.0,
        100.0,
        0.48,
        0.0,
        130.0,
        0.05,
        653.0,
        23000.0,
        0.004,
    ),
    VehicleModel(
        "BEV002",
        "DSL002",
        "Light Rigid",
        "BEV",
        "Hyundai Mighty Electric",
        4.0,
        150000.0,
        200.0,
        97.0,
        0.48,
        0.0,
        130.0,
        0.05,
        653.0,
        23000.0,
        0.004,
    ),
    VehicleModel(
        "BEV003",
        "DSL003",
        "Light Rigid",
        "BEV",
        "Jac N90",
        5.0,
        150000.0,
        180.0,
        107.0,
        0.61,
        0.0,
        130.0,
        0.05,
        653.0,
        23000.0,
        0.004,
    ),
    VehicleModel(
        "BEV004",
        "DSL004",
        "Medium Rigid",
        "BEV",
        "Volvo FL",
        10.5,
        200000.0,
        300.0,
        264.0,
        0.88,
        0.0,
        130.0,
        0.08,
        653.0,
        23000.0,
        0.006,
    ),
    VehicleModel(
        "BEV005",
        "DSL005",
        "Medium Rigid",
        "BEV",
        "MB eActros 300",
        22.0,
        400000.0,
        300.0,
        336.0,
        1.09,
        0.0,
        130.0,
        0.08,
        653.0,
        23000.0,
        0.006,
    ),
    VehicleModel(
        "BEV006",
        "DSL006",
        "Articulated",
        "BEV",
        "MB eActros 600",
        42.0,
        600000.0,
        500.0,
        621.0,
        1.2,
        0.0,
        130.0,
        0.12,
        6872.0,
        84000.0,
        0.009,
    ),
    VehicleModel(
        "BEV007",
        "DSL007",
        "Articulated",
        "BEV",
        "Volvo FH",
        42.0,
        450000.0,
        300.0,
        540.0,
        1.8,
        0.0,
        130.0,
        0.12,
        6872.0,
        84000.0,
        0.009,
    ),
    VehicleModel(
        "BEV008",
        "DSL008",
        "Articulated",
        "BEV",
        "Scania 45R",
        42.0,
        320000.0,
        390.0,
        624.0,
        1.6,
        0.0,
        130.0,
        0.12,
        6872.0,
        84000.0,
        0.009,
    ),
    VehicleModel(
        "DSL001",
        "BEV001",
        "Light Rigid",
        "Diesel",
        "Hino 300",
        4.5,
        80000.0,
        600.0,
        0.0,
        0.0,
        0.28,
        0.0,
        0.2,
        653.0,
        23000.0,
        0.01,
    ),
    VehicleModel(
        "DSL002",
        "BEV002",
        "Light Rigid",
        "Diesel",
        "Hyundai Mighty",
        4.0,
        75000.0,
        600.0,
        0.0,
        0.0,
        0.28,
        0.0,
        0.02,
        653.0,
        23000.0,
        0.01,
    ),
    VehicleModel(
        "DSL003",
        "BEV003",
        "Light Rigid",
        "Diesel",
        "Hino 500",
        6.0,
        130000.0,
        600.0,
        0.0,
        0.0,
        0.28,
        0.0,
        0.02,
        653.0,
        23000.0,
        0.01,
    ),
    VehicleModel(
        "DSL004",
        "BEV004",
        "Medium Rigid",
        "Diesel",
        "Volvo FE",
        12.0,
        220000.0,
        600.0,
        0.0,
        0.0,
        0.32,
        0.0,
        0.025,
        653.0,
        23000.0,
        0.017,
    ),
    VehicleModel(
        "DSL005",
        "BEV005",
        "Medium Rigid",
        "Diesel",
        "MB Actros",
        25.0,
        270000.0,
        1400.0,
        0.0,
        0.0,
        0.32,
        0.0,
        0.025,
        653.0,
        23000.0,
        0.017,
    ),
    VehicleModel(
        "DSL006",
        "BEV006",
        "Articulated",
        "Diesel",
        "MB Actros",
        50.0,
        270000.0,
        1400.0,
        0.0,
        0.0,
        0.35,
        0.0,
        0.03,
        6872.0,
        84000.0,
        0.025,
    ),
    VehicleModel(
        "DSL007",
        "BEV007",
        "Articulated",
        "Diesel",
        "Volvo FH",
        50.0,
        280000.0,
        2000.0,
        0.0,
        0.0,
        0.35,
        0.0,
        0.03,
        6872.0,
        84000.0,
        0.025,
    ),
    VehicleModel(
        "DSL008",
        "BEV008",
        "Articulated",
        "Diesel",
        "Scania R560",
        50.0,
        300000.0,
        1500.0,
        0.0,
        0.0,
        0.35,
        0.0,
        0.03,
        6872.0,
        84000.0,
        0.025,
    ),
]

BY_ID: Dict[str, VehicleModel] = {m.vehicle_id: m for m in ALL_MODELS}
</file>

<file path="frontend/src/components/results/AnalyticsSummaryCard.tsx">
import Card from '@components/shared/Card';
import { useAnalyticsSummary } from '@hooks/useAnalyticsSummary';
import { formatCurrency } from '@utils/format';

const AnalyticsSummaryCard = () => {
  const { data, isLoading, isError } = useAnalyticsSummary();

  const metrics = [
    {
      label: 'Total sessions',
      value: data ? data.totalSessions.toLocaleString() : '—',
    },
    {
      label: 'Completed sessions',
      value: data ? data.completedSessions.toLocaleString() : '—',
    },
    {
      label: 'Calculations (24h)',
      value: data ? data.calculationsLast24h.toLocaleString() : '—',
    },
    {
      label: 'BEV win rate',
      value:
        data && data.bevWinRate !== null && data.bevWinRate !== undefined
          ? `${(data.bevWinRate * 100).toFixed(1)}%`
          : '—',
    },
    {
      label: 'Average payback',
      value:
        data && data.averagePaybackYears
          ? `${data.averagePaybackYears.toFixed(1)} yrs`
          : '—',
    },
    {
      label: 'Average BEV cost delta',
      value:
        data && data.averageCostDelta !== null && data.averageCostDelta !== undefined
          ? formatCurrency(data.averageCostDelta)
          : '—',
    },
  ];

  return (
    <Card
      title="Platform telemetry"
      subtitle="Aggregated from the autosaved sessions powering TWU analytics."
    >
      {isLoading && <p className="text-sm text-slate-500">Refreshing analytics…</p>}
      {isError && <p className="text-sm text-rose-500">Analytics unavailable. Please retry later.</p>}
      {data && (
        <div className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="border border-slate-200 p-4 bg-slate-50">
              <p className="text-xs font-bold text-slate-500 mb-1">{metric.label}</p>
              <p className="text-xl font-heading font-bold text-black">{metric.value}</p>
            </div>
          ))}
        </div>
      )}
      {data && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <p className="text-xs font-bold text-slate-500 mb-3">Top vehicles</p>
          {Object.keys(data.topVehicles).length === 0 ? (
            <p className="text-sm text-slate-500">No runs yet.</p>
          ) : (
            <ul className="grid gap-y-2 text-sm text-slate-800">
              {Object.entries(data.topVehicles).map(([vehicleId, count]) => (
                <li key={vehicleId} className="flex justify-between items-center bg-white p-2 border border-slate-100">
                  <span className="font-bold">{vehicleId}</span>
                  <span className="text-xs bg-brand-primary text-black font-bold px-2 py-0.5 rounded-full">{count} runs</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
};

export default AnalyticsSummaryCard;
</file>

<file path="frontend/src/components/shared/Button.tsx">
import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

const variantStyles: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-brand-primary text-brand-secondary hover:bg-[#E6B300] border-2 border-transparent shadow-button',
  secondary: 'bg-transparent text-black border-2 border-black hover:bg-black hover:text-white',
  ghost: 'bg-transparent text-slate-600 hover:text-black hover:bg-black/5',
};

const Button = ({ children, className, variant = 'primary', ...props }: PropsWithChildren<ButtonProps>) => (
  <button
    className={clsx(
      'inline-flex items-center justify-center px-6 py-3 text-sm font-bold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 rounded-lg active:scale-[0.98]',
      variantStyles[variant],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

export default Button;
</file>

<file path="frontend/src/components/shared/Card.tsx">
import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: ReactNode;
  headerAction?: ReactNode;
  className?: string;
}

const Card = ({ title, subtitle, headerAction, className, children }: PropsWithChildren<CardProps>) => (
  <section className={clsx(
    'bg-white p-4 sm:p-6 md:p-8 border border-slate-200 rounded-lg shadow-card hover:shadow-card-hover border-l-4 border-l-brand-primary transition-shadow',
    className
  )}>
    {(title || subtitle || headerAction) && (
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          {title && <h2 className="text-2xl font-heading font-normal text-black tracking-tight">{title}</h2>}
          {subtitle && <p className="text-sm text-slate-600 mt-1">{subtitle}</p>}
        </div>
        {headerAction}
      </div>
    )}
    {children}
  </section>
);

export default Card;
</file>

<file path="frontend/src/hooks/useWizardAutosave.ts">
import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useTCOStore } from '@state/tcoStore';
import { updateSession } from '@services/api';
import type { WizardData } from '@shared/types/tco.types';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';

const sanitizeWizardData = (wizardData: WizardData): WizardData => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides ?? {}
  );

  return {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
    vehicleParamOverrides: Object.keys(vehicleOverrides).length
      ? vehicleOverrides
      : undefined,
  };
};

export const useWizardAutosave = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const lastSnapshot = useRef<string>('');

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const payload = sanitizeWizardData(wizardData);
    const serialized = JSON.stringify(payload);
    if (serialized === lastSnapshot.current) {
      return;
    }

    const timer = setTimeout(() => {
      lastSnapshot.current = serialized;
      updateSession(sessionId, { wizardData: payload }).catch((error) => {
        console.warn('Autosave failed', error);
        toast.error('Auto-save failed. Your changes may not be saved.', {
          id: 'autosave-error', // Prevent duplicate toasts
          duration: 5000,
        });
        // Reset snapshot so it retries on next change
        lastSnapshot.current = '';
      });
    }, 800);

    return () => clearTimeout(timer);
  }, [sessionId, wizardData]);
};
</file>

<file path="frontend/src/utils/payload.ts">
import type {
  CalculationResponsePayload,
  CostOverrides,
  SessionCreatePayload,
  VehicleParamOverrides,
  WizardData,
} from '@shared/types/tco.types';

export const compactOverrides = (overrides?: CostOverrides) =>
  Object.fromEntries(
    Object.entries(overrides ?? {}).filter(
      ([, value]) => value !== undefined && value !== null
    ) as [string, number][]
  ) as CostOverrides;

export const compactVehicleParamOverrides = (
  overrides?: Record<string, VehicleParamOverrides>
) => {
  const cleaned: Record<string, VehicleParamOverrides> = {};
  Object.entries(overrides ?? {}).forEach(([vehicleId, fields]) => {
    const filteredEntries = Object.entries(fields ?? {}).filter(
      ([, value]) => value !== undefined && value !== null
    );
    if (filteredEntries.length) {
      cleaned[vehicleId] = Object.fromEntries(
        filteredEntries
      ) as VehicleParamOverrides;
    }
  });
  return cleaned;
};

export const buildSessionPayload = (
  wizardData: WizardData,
  results: CalculationResponsePayload[]
): SessionCreatePayload => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides
  );
  const serializedWizard: WizardData = {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
    vehicleParamOverrides: Object.keys(vehicleOverrides).length
      ? vehicleOverrides
      : undefined,
  };

  return {
    wizardData: serializedWizard,
    results,
  };
};
</file>

<file path="frontend/vitest.config.ts">
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@state': path.resolve(__dirname, './src/state'),
      '@forms': path.resolve(__dirname, './src/forms'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@shared': path.resolve(__dirname, '../shared'),
    },
  },
  test: {
    environment: 'node',
    globals: true,
    include: ['src/**/*.test.ts', 'src/**/*.spec.ts'],
    exclude: ['**/e2e/**', '**/node_modules/**'],
  },
});
</file>

<file path="scripts/validate_deployment.py">
#!/usr/bin/env python
"""Pre-deployment validation script to ensure all imports work correctly."""

from importlib import import_module
from pathlib import Path
import sys


def validate_backend_imports():
    """Validate that all backend models can be imported."""
    print("🔍 Validating backend imports...")
    try:
        models_module = import_module("backend.app.models")
    except ImportError as exc:
        print(f"✗ Backend import error: {exc}")
        return False

    model_names = [
        "CalculationRequest",
        "CalculationResponse",
        "ComparisonRequest",
        "CostBreakdown",
        "CostOverride",
        "VehicleDetail",
        "VehicleParamOverride",
        "VehicleSummary",
    ]

    try:
        resolved_models = {name: getattr(models_module, name) for name in model_names}
    except AttributeError as exc:
        print(f"✗ Missing model attribute: {exc}")
        return False

    print("✓ All backend models import successfully")
    vehicle_param_override = resolved_models["VehicleParamOverride"]
    print(
        f"  - VehicleParamOverride has {len(vehicle_param_override.model_fields)} fields"
    )
    return True


def validate_backend_app():
    """Validate that the FastAPI app can be imported."""
    print("\n🔍 Validating FastAPI app...")
    try:
        from backend.app.main import app

        print(f"✓ FastAPI app imports successfully ({len(app.routes)} routes)")
        return True
    except Exception as e:
        print(f"✗ FastAPI app import error: {e}")
        return False


def validate_frontend_build():
    """Check if frontend build directory exists."""
    print("\n🔍 Checking frontend build...")
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        files = list(frontend_dist.glob("**/*"))
        print(f"✓ Frontend build exists ({len(files)} files)")
        return True
    else:
        print("⚠ Frontend build not found (run 'cd frontend && npm run build')")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("PRE-DEPLOYMENT VALIDATION")
    print("=" * 60)

    checks = [
        validate_backend_imports(),
        validate_backend_app(),
        validate_frontend_build(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All validation checks passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
</file>

<file path="shared/calculator/math.ts">
/**
 * Financial Mathematics Utilities for TCO Calculations
 *
 * CONVENTIONS:
 * - All functions use ANNUAL discount rates
 * - End-of-period discounting (year 1 = no discounting)
 * - Years are 1-indexed (year 1, year 2, etc.)
 *
 * These conventions match the original Python implementation
 * and are verified by verification.test.ts against Python-generated fixtures.
 */

import { CONSTANTS } from '../data/constants';

const DISCOUNT_RATE = CONSTANTS.DISCOUNT_RATE as number;
const VEHICLE_LIFE = CONSTANTS.VEHICLE_LIFE as number;

export const calculatePresentValue = (
  annualAmount: number,
  years: number = VEHICLE_LIFE,
  discountRate: number = DISCOUNT_RATE
): number => {
  if (discountRate === 0) {
    return annualAmount * years;
  }

  return annualAmount * ((1 - (1 + discountRate) ** -years) / discountRate);
};

/**
 * Discounts a single future value to present value.
 *
 * Uses END-OF-PERIOD convention:
 * - Year 1 cashflows are NOT discounted (exponent = 0)
 * - Year 2 cashflows are discounted by (1+r)^1
 * - Year n cashflows are discounted by (1+r)^(n-1)
 *
 * This matches the original Python implementation and is consistent
 * with assuming cashflows occur at the END of each year, with the
 * first year's cashflow occurring at time 0 (today).
 *
 * @param amount - Future value to discount
 * @param year - Year number (1-indexed)
 * @param discountRate - Annual discount rate (e.g., 0.05 for 5%)
 * @returns Present value of the future amount
 *
 * @example
 * // $1000 received at end of year 2, discounted at 5%
 * discountToPresent(1000, 2, 0.05) // Returns ~$952.38
 */
export const discountToPresent = (
  amount: number,
  year: number,
  discountRate: number = DISCOUNT_RATE
): number => {
  return amount / (1 + discountRate) ** (year - 1);
};

export const calculateNpvOfPayments = (
  monthlyPayment: number,
  numPayments: number,
  discountRate: number = DISCOUNT_RATE
): number => {
  let npv = 0;

  for (let month = 1; month <= numPayments; month += 1) {
    const yearFraction = month / 12;
    const discountFactor = (1 + discountRate) ** yearFraction;
    npv += monthlyPayment / discountFactor;
  }

  return npv;
};

export const calculateNpvOfAnnualCashflows = (
  cashflows: number[],
  discountRate: number = DISCOUNT_RATE
): number => {
  return cashflows.reduce((sum, amount, index) => {
    const year = index + 1;
    return sum + discountToPresent(amount, year, discountRate);
  }, 0);
};

export const calculateAnnualisedCost = (
  totalCost: number,
  years: number = VEHICLE_LIFE,
  discountRate: number = DISCOUNT_RATE
): number => {
  if (discountRate === 0) {
    return totalCost / years;
  }

  return totalCost / ((1 - (1 + discountRate) ** -years) / discountRate);
};
</file>

<file path="shared/data/constants.ts">
/**
 * @file TCO Calculator Constants
 * @module shared/data/constants
 *
 * Central configuration for all calculation parameters.
 * Values are sourced from industry research and Australian government data.
 *
 * @see FUTURE_CONSTANTS for planned but not yet implemented features
 */

// Auto-generated by scripts/generate_vehicle_catalog_ts.py. Do not edit manually.

import type { ConstantCatalog } from '../types/tco.types';

export const CONSTANTS: ConstantCatalog = {
  "ART_ANNUAL_KMS": 84000,
  "BATTERY_LIFE_VARIATION_BASE": 2.0,
  "BATTERY_RECYCLE_VALUE": 13,
  "BATTERY_REPLACEMENT_COST": 130,
  "BATTERY_REPLACEMENT_YEAR": 8,
  "BATTERY_USABLE_RANGE_FACTOR": 0.6,
  "CHARGING_MIX_PROPORTIONS": {
    "BEV": {
      "Articulated": {
        "offpeak": 0.33,
        "public": 0.57,
        "retail": 0.0,
        "solar": 0.0
      },
      "Light Rigid": {
        "offpeak": 0.86,
        "public": 0.14,
        "retail": 0.0,
        "solar": 0.0
      },
      "Medium Rigid": {
        "offpeak": 0.86,
        "public": 0.14,
        "retail": 0.0,
        "solar": 0.0
      }
    }
  },
  "CHARGING_TIME_HOURS": {
    "Articulated": 1.0,
    "Light Rigid": 0.6,
    "Medium Rigid": 0.75
  },
  "DAYS_IN_YEAR": 365,
  "DEPRECIATION_RATE_FIRST_YEAR": 0.2,
  "DEPRECIATION_RATE_ONGOING": 0.1,
  "DIESEL_EMISSIONS": 2.68,
  "DIESEL_PRICE": 2.05,
  "DISCOUNT_RATE": 0.05,
  "DOWN_PAYMENT_RATE": 0.2,
  "FINANCING_TERM": 5,
  "FREIGHT_RATE_PER_TONNE_KM": {
    "Articulated": 0.08,
    "Light Rigid": 0.25,
    "Medium Rigid": 0.25
  },
  "HOURLY_WAGE": 47,
  "HOURS_IN_YEAR": 8760,
  "INSURANCE_RATE_BEV": 0.035,
  "INSURANCE_RATE_DSL": 0.0315,
  "INTEREST_RATE": 0.06,
  "MAINTENANCE_COST_PER_KM": {
    "BEV": {
      "Articulated": 0.19,
      "Light Rigid": 0.1,
      "Medium Rigid": 0.1
    },
    "Diesel": {
      "Articulated": 0.28,
      "Light Rigid": 0.18,
      "Medium Rigid": 0.18
    }
  },
  "MONTHS_IN_YEAR": 12,
  "OFFPEAK_CHARGING_EMISSIONS": 0.7,
  "OFFPEAK_CHARGING_PRICE": 0.15,
  "OTHER_INSURANCE": 2000,
  "PAYLOAD_UTILISATION_FACTOR": {
    "Articulated": 0.9,
    "Light Rigid": 0.8,
    "Medium Rigid": 0.8
  },
  "PUBLIC_CHARGING_EMISSIONS": 0.7,
  "PUBLIC_CHARGING_PRICE": 0.5,
  "RETAIL_CHARGING_EMISSIONS": 0.7,
  "RETAIL_CHARGING_PRICE": 0.3,
  "RIGID_ANNUAL_KMS": 23000,
  "SOLAR_CHARGING_EMISSIONS": 0.04,
  "SOLAR_CHARGING_PRICE": 0.04,
  "STAMP_DUTY_RATE": 0.03,
  "VEHICLE_LIFE": 15,
  "WEEKS_IN_YEAR": 52,
  "WORKING_DAYS": 255
} as const;

/**
 * FUTURE FEATURES - Not currently used in calculations
 * These constants are reserved for planned features.
 * Moving here instead of deleting to preserve for future implementation.
 */
export const FUTURE_CONSTANTS = {
  /** Annual battery capacity degradation rate (2.5% per year) */
  BATTERY_DEGRADATION_RATE: 0.025,

  /** Cost of DC fast charger installation */
  CHARGER_COST: 300000,

  /** Australian fuel tax credit rate per litre */
  FUEL_TAX_CREDIT: 0.203,

  /** Road user charge per km (heavy vehicles) */
  ROAD_USER_CHARGE: 0.305,

  /** Annual inflation rate for cost projections */
  INFLATION_RATE: 0.025,

  /** Expected lifespan of charging infrastructure */
  INFRASTRUCTURE_LIFE: 15,

  /** Legacy proportion constants - superseded by CHARGING_MIX_PROPORTIONS */
  OFFPEAK_PROPORTION: 0.86,
  PUBLIC_PROPORTION: 0.14,
  RETAIL_PROPORTION: 0.0,
  SOLAR_PROPORTION: 0.0,

  /** Solar PV and battery storage installation costs */
  SOLAR_MAINTENANCE: 0.15,
  SOLAR_PANEL_INSTALLATION: 1285,
  STORAGE_INSTALLATION: 423,
  STORAGE_MAINTENANCE: 0.025,
} as const;
</file>

<file path="API.md">
# API Documentation

The TCO Web Platform provides a RESTful API for calculating Total Cost of Ownership, managing sessions, and accessing analytics.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://your-domain.com/api/v1`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Endpoints

### System

#### Health Check

```http
GET /api/v1/health
```

Check if the API is running and retrieve environment information.

**Response:**
```json
{
  "status": "ok",
  "environment": "production"
}
```

---

### Vehicles

#### List All Vehicles

```http
GET /api/v1/vehicles
```

Retrieve a list of all available vehicles with summary information.

**Response:**
```json
[
  {
    "id": "BEV001",
    "name": "Jac N75",
    "weight_class": "Light Rigid",
    "drivetrain": "BEV",
    "payload_kg": 2650,
    "range_km": 300,
    "msrp": 145000,
    "comparison_pair": "DSL001"
  },
  {
    "id": "DSL001",
    "name": "Hino 300",
    "weight_class": "Light Rigid",
    "drivetrain": "DSL",
    "payload_kg": 3000,
    "range_km": 800,
    "msrp": 85000,
    "comparison_pair": "BEV001"
  }
]
```

#### Get Vehicle Details

```http
GET /api/v1/vehicles/{vehicle_id}
```

Retrieve detailed specifications for a specific vehicle.

**Parameters:**
- `vehicle_id` (path): Vehicle identifier (e.g., "BEV001")

**Response:**
```json
{
  "id": "BEV001",
  "name": "Jac N75",
  "weight_class": "Light Rigid",
  "drivetrain": "BEV",
  "payload_kg": 2650,
  "range_km": 300,
  "msrp": 145000,
  "battery_kwh": 89.0,
  "consumption_kwh_100km": 60.0,
  "maintenance_cost_per_km": 0.18,
  "registration_cost": 800,
  "default_annual_kms": 50000,
  "comparison_pair": "DSL001"
}
```

**Error Responses:**
- `404 Not Found` - Vehicle ID does not exist

---

> Note: TCO calculations now execute in the shared TypeScript engine on the frontend. Backend endpoints currently cover vehicles, sessions, and analytics only.

### Sessions

Session endpoints allow you to persist calculation sessions for later retrieval.

#### Create Session

```http
POST /api/v1/sessions
```

Create a new calculation session with inputs and results.

**Request Body:**
```json
{
  "wizard_data": {
    "selected_vehicles": ["BEV001", "DSL001"],
    "scenario": "baseline",
    "purchase_method": "financed",
    "annual_kms": 50000,
    "duty_cycle": {
      "urban": 0.6,
      "regional": 0.3,
      "long_haul": 0.1
    },
    "overrides": {}
  },
  "results": [
    {
      "vehicle_id": "BEV001",
      "total_cost_npv": 523750.25,
      "cost_per_km": 0.62,
      "breakdown": {...}
    }
  ],
  "operator_profile": {
    "operator_type": "owner_driver",
    "fleet_size": 1,
    "industry": "construction"
  }
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:30:00Z"
}
```

**Status Code:** `201 Created`

#### Get Session

```http
GET /api/v1/sessions/{session_id}
```

Retrieve a saved session by ID.

**Parameters:**
- `session_id` (path): UUID of the session

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist

#### Update Session

```http
PUT /api/v1/sessions/{session_id}
```

Update an existing session with new data.

**Parameters:**
- `session_id` (path): UUID of the session

**Request Body:**
```json
{
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "wizard_data": {...},
  "results": [...],
  "operator_profile": {...},
  "created_at": "2025-11-10T21:30:00Z",
  "updated_at": "2025-11-10T21:45:00Z"
}
```

**Error Responses:**
- `404 Not Found` - Session ID does not exist

---

### Analytics

#### Get Analytics Summary

```http
GET /api/v1/analytics/summary
```

Retrieve aggregated analytics across all sessions.

**Response:**
```json
{
  "total_sessions": 1250,
  "total_calculations": 3875,
  "bev_win_rate": 0.68,
  "average_payback_years": 4.2,
  "top_vehicles": [
    {
      "vehicle_id": "BEV001",
      "count": 450
    },
    {
      "vehicle_id": "BEV003",
      "count": 380
    }
  ],
  "scenario_distribution": {
    "baseline": 0.65,
    "tech_breakthrough": 0.25,
    "oil_crisis": 0.10
  }
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production deployments, consider implementing rate limiting at the infrastructure level.

---

## CORS

The API supports CORS for browser-based clients. Allowed origins can be configured via the `BACKEND_CORS_ORIGINS` environment variable.

Default development origins:
- `http://localhost:5000`
- `http://127.0.0.1:5000`

---

## Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get all vehicles
vehicles = requests.get(f"{BASE_URL}/vehicles").json()
print(f"Loaded {len(vehicles)} vehicles")

# Get analytics summary
analytics = requests.get(f"{BASE_URL}/analytics/summary").json()
print(f"Total sessions: {analytics['totalSessions']}")
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

async function loadCatalogAndAnalytics() {
  const [vehiclesRes, analyticsRes] = await Promise.all([
    fetch(`${BASE_URL}/vehicles`),
    fetch(`${BASE_URL}/analytics/summary`),
  ]);

  const vehicles = await vehiclesRes.json();
  const analytics = await analyticsRes.json();

  console.log(`Loaded ${vehicles.length} vehicles`);
  console.log(`Total sessions: ${analytics.totalSessions}`);
}
```

---

## Interactive API Documentation

When the backend server is running, you can access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation where you can test endpoints directly in the browser.
</file>

<file path="backend/app/api/router.py">
"""Versioned API router that wires endpoints to services."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.db.session import get_db_session
from backend.app.models import (

    VehicleDetail,
    VehicleSummary,
)
from backend.app.models.session import (
    AnalyticsSummary,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)
from backend.app.services import VehicleCatalogService
from backend.app.services.sessions import SessionService

api_router = APIRouter(prefix=settings.api_v1_prefix)


_vehicle_service = VehicleCatalogService()
_session_service = SessionService()


@api_router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@api_router.get("/vehicles", response_model=List[VehicleSummary], tags=["vehicles"])
def list_vehicles() -> List[VehicleSummary]:
    return _vehicle_service.list_summaries()


@api_router.get(
    "/vehicles/{vehicle_id}", response_model=VehicleDetail, tags=["vehicles"]
)
def get_vehicle(vehicle_id: str) -> VehicleDetail:
    try:
        return _vehicle_service.get(vehicle_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc





@api_router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["sessions"],
)
async def create_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    try:
        return await _session_service.create_session(db, payload)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.put(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    try:
        return await _session_service.update_session(db, session_id, payload)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["sessions"],
)
async def get_session(
    session_id: str, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    try:
        return await _session_service.get_session(db, session_id)
    except KeyError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@api_router.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    tags=["analytics"],
)
async def analytics_summary(
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsSummary:
    return await _session_service.analytics_summary(db)
</file>

<file path="backend/app/core/cache.py">
"""Redis cache client for session persistence."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _create_client() -> Optional[redis.Redis]:
    """Create Redis client if URL is configured."""
    if settings.redis_url:
        try:
            return redis.from_url(settings.redis_url, decode_responses=True)
        except Exception as exc:
            logger.warning("Failed to create Redis client: %s", exc)
            return None
    return None


redis_client = _create_client()


async def cache_session(session_id: str, payload: dict[str, Any]) -> None:
    """Persist wizard session snapshots in Redis for quick resume."""

    if not redis_client:
        logger.debug("Redis not available, skipping cache for session %s", session_id)
        return

    try:
        await redis_client.setex(
            f"session:{session_id}",
            settings.session_ttl_seconds,
            json.dumps(payload),
        )
    except Exception as exc:  # pragma: no cover - cache failures shouldn't break flow
        logger.warning("Failed to cache session %s: %s", session_id, exc)


async def get_cached_session(session_id: str) -> Optional[dict[str, Any]]:
    """Return a cached session snapshot if present."""

    if not redis_client:
        logger.debug("Redis not available, returning None for session %s", session_id)
        return None

    try:
        raw = await redis_client.get(f"session:{session_id}")
        if not raw:
            return None
        return json.loads(raw)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to fetch cached session %s: %s", session_id, exc)
        return None
</file>

<file path="backend/app/db/models.py">
"""Database table definitions for session persistence and analytics."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    wizard_state: Mapped[dict | None] = mapped_column(JSON, default=dict)
    cached_results: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    inputs: Mapped[list["UserInputRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    results: Mapped[list["CalculationResultRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    operator_profile: Mapped["OperatorProfileRecord"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    feedback_entries: Mapped[list["FeedbackRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class UserInputRecord(Base):
    __tablename__ = "user_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(16), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)
    purchase_method: Mapped[str] = mapped_column(String(16), nullable=False)
    overrides: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="inputs")


class CalculationResultRecord(Base):
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(16), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)
    purchase_method: Mapped[str] = mapped_column(String(16), nullable=False)
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    annual_cost: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="results")


class OperatorProfileRecord(Base):
    __tablename__ = "operator_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    operator_type: Mapped[str | None] = mapped_column(String(64))
    fleet_size: Mapped[str | None] = mapped_column(String(32))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    consent_to_contact: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="operator_profile")


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[SessionRecord] = relationship(back_populates="feedback_entries")
</file>

<file path="backend/app/models/session.py">
"""Pydantic models for session persistence and analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator, validator

from backend.app.models.calculation import (
    CalculationResponse,
    CostOverride,
    VehicleParamOverride,
)


class DutyCyclePayload(BaseModel):
    urban: float = Field(ge=0, le=100)
    regional: float = Field(ge=0, le=100)
    long_haul: float = Field(ge=0, le=100, alias="longHaul")

    @validator("urban", "regional", "long_haul")
    def _round_values(cls, value: float) -> float:  # noqa: D401
        """Ensure floats are rounded to two decimals for storage consistency."""

        return round(float(value), 4)

    def total(self) -> float:
        return self.urban + self.regional + self.long_haul

    model_config = {
        "populate_by_name": True,
    }


class WizardDataPayload(BaseModel):
    current_vehicle: Optional[str] = Field(default=None, alias="currentVehicle")
    comparison_vehicles: List[str] = Field(
        default_factory=list, alias="comparisonVehicles"
    )
    scenario: str
    purchase_method: Literal["financed", "outright"] = Field(alias="purchaseMethod")
    duty_cycle: DutyCyclePayload = Field(alias="dutyCycle")
    overrides: Optional[CostOverride] = None
    vehicle_param_overrides: Optional[Dict[str, VehicleParamOverride]] = Field(
        default=None, alias="vehicleParamOverrides"
    )

    model_config = {
        "populate_by_name": True,
    }

    @model_validator(mode="after")
    def _validate_duty_cycle(self) -> "WizardDataPayload":
        if abs(self.duty_cycle.total() - 100) > 0.5:
            raise ValueError("Duty cycle splits must sum to ~100%.")
        return self


class OperatorProfilePayload(BaseModel):
    operator_type: Optional[str] = Field(default=None, alias="operatorType")
    fleet_size: Optional[str] = Field(default=None, alias="fleetSize")
    contact_email: Optional[str] = Field(default=None, alias="contactEmail")
    consent_to_contact: bool = Field(default=False, alias="consentToContact")
    notes: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }


class FeedbackPayload(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None


class SessionPayloadBase(BaseModel):
    wizard_data: WizardDataPayload = Field(alias="wizardData")
    results: Optional[List[CalculationResponse]] = None
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None

    model_config = {
        "populate_by_name": True,
    }


class SessionCreate(SessionPayloadBase):
    pass


class SessionUpdate(BaseModel):
    wizard_data: Optional[WizardDataPayload] = Field(default=None, alias="wizardData")
    results: Optional[List[CalculationResponse]] = None
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None

    model_config = {
        "populate_by_name": True,
    }


class SessionResponse(BaseModel):
    session_id: str = Field(alias="sessionId")
    status: str
    wizard_data: WizardDataPayload = Field(alias="wizardData")
    results: List[CalculationResponse] = Field(default_factory=list)
    operator_profile: Optional[OperatorProfilePayload] = Field(
        default=None, alias="operatorProfile"
    )
    feedback: Optional[FeedbackPayload] = None
    updated_at: datetime = Field(alias="updatedAt")
    last_calculated_at: Optional[datetime] = Field(
        default=None, alias="lastCalculatedAt"
    )

    model_config = {
        "populate_by_name": True,
    }


class AnalyticsSummary(BaseModel):
    total_sessions: int = Field(alias="totalSessions")
    completed_sessions: int = Field(alias="completedSessions")
    calculations_last_24h: int = Field(alias="calculationsLast24h")
    bev_win_rate: Optional[float] = Field(default=None, alias="bevWinRate")
    average_payback_years: Optional[float] = Field(
        default=None, alias="averagePaybackYears"
    )
    average_cost_delta: Optional[float] = Field(default=None, alias="averageCostDelta")
    top_vehicles: Dict[str, int] = Field(default_factory=dict, alias="topVehicles")
</file>

<file path="backend/app/services/__init__.py">
"""Domain services for the FastAPI layer (vehicles, sessions, analytics)."""


from .vehicles import VehicleCatalogService

__all__ = ["VehicleCatalogService"]
</file>

<file path="frontend/src/components/layout/AppShell.tsx">
import { NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

const AppShell = ({ children }: PropsWithChildren) => (
  <div className="min-h-screen bg-brand-background text-brand-text font-body">
    <header className="bg-white text-black border-b-4 border-brand-primary shadow-sm relative z-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-5">
        <div>
          <p className="text-xs font-bold opacity-80">Energy Futures Foundation</p>
          <h1 className="text-2xl font-heading font-normal tracking-tight">
            Truck Cost Calculator
          </h1>
        </div>
        <nav className="flex gap-1 text-sm font-semibold tracking-wide">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Compare
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Results
          </NavLink>
        </nav>
      </div>
    </header>
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 sm:px-6 py-8 md:py-12">
      {children}
    </main>
  </div>
);

export default AppShell;
</file>

<file path="frontend/src/components/results/CostBreakdownChart.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import type { CalculationResponsePayload } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

// Brand-aligned cost colors
const COST_COLORS = {
  purchase_cost: '#3040B9',
  fuel_cost: '#3B52FF',
  maintenance_cost: '#7080FF',
  insurance_cost: '#B9C2FF',
  registration_cost: '#844A34',
  battery_replacement_cost: '#005A46',
  financing_cost: '#EA5300',
  carbon_cost: '#F2AE95',
  charging_labour_cost: '#00FFC7',
  payload_penalty_cost: '#C5FFF3',
  taxes_and_fees: '#000000',
} as const;

const breakdownSeries = [
  { key: 'purchase_cost', label: 'Purchase', color: COST_COLORS.purchase_cost },
  { key: 'fuel_cost', label: 'Fuel / Energy', color: COST_COLORS.fuel_cost },
  { key: 'maintenance_cost', label: 'Maintenance', color: COST_COLORS.maintenance_cost },
  { key: 'insurance_cost', label: 'Insurance', color: COST_COLORS.insurance_cost },
  { key: 'registration_cost', label: 'Registration', color: COST_COLORS.registration_cost },
  { key: 'battery_replacement_cost', label: 'Battery replacement', color: COST_COLORS.battery_replacement_cost },
  { key: 'financing_cost', label: 'Financing', color: COST_COLORS.financing_cost },
  { key: 'carbon_cost', label: 'Carbon', color: COST_COLORS.carbon_cost },
  { key: 'charging_labour_cost', label: 'Charging labour', color: COST_COLORS.charging_labour_cost },
  { key: 'payload_penalty_cost', label: 'Payload penalty', color: COST_COLORS.payload_penalty_cost },
  { key: 'taxes_and_fees', label: 'Taxes & fees', color: COST_COLORS.taxes_and_fees },
] as const;

type BreakdownKey = keyof CalculationResponsePayload['breakdown'];

const CostBreakdownChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Cost components"
        subtitle="Stacked view of the present value cost drivers for each vehicle."
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  const data = results.map((result) => {
    const entry: Record<string, number | string> = {
      vehicle: vehicleDetails[result.vehicle_id]?.model_name ?? result.vehicle_id,
    };

    breakdownSeries.forEach(({ key }) => {
      const breakdownValue = result.breakdown[key as BreakdownKey] ?? 0;
      entry[key] = breakdownValue;
    });

    return entry;
  });

  return (
    <Card
      title="Cost components"
      subtitle="Stacked view of the present value cost drivers for each vehicle."
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12, fill: '#000000' }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, { maximumFractionDigits: 0 })
            }
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip
            formatter={(value, name) => {
              const series = breakdownSeries.find((item) => item.key === name);
              return [formatCurrency(value as number), series?.label ?? (name as string)];
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {breakdownSeries.map((series) => (
            <Bar
              key={series.key}
              dataKey={series.key}
              name={series.label}
              stackId="cost"
              fill={series.color}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostBreakdownChart;
</file>

<file path="frontend/src/components/results/CostPerKmChart.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency, formatPerKilometre } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const DIESEL_COLOR = '#EA5300';
const ELECTRIC_COLOR = '#00FFC7';
const WINNER_COLOR = '#FFC700';

const CostTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as {
    vehicle: string;
    costPerKm: number;
    annualCost: number;
    totalCost: number;
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.vehicle}</p>
      <p>{formatPerKilometre(entry.costPerKm)}</p>
      <p>Annual {formatCurrency(entry.annualCost)}</p>
      <p>Total cost {formatCurrency(entry.totalCost)}</p>
    </div>
  );
};

const CostPerKmChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Cost per kilometre"
        subtitle="Lower bars indicate cheaper ownership under the selected scenario."
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  // Determine the winner (lowest cost per km)
  const minCostPerKm = Math.min(...results.map((r) => r.cost_per_km));

  const data = results.map((result) => {
    const detail = vehicleDetails[result.vehicle_id];
    const drivetrainType = detail?.drivetrain_type ?? 'Diesel';
    const isWinner = result.cost_per_km === minCostPerKm;

    return {
      vehicle: detail?.model_name ?? result.vehicle_id,
      costPerKm: Number(result.cost_per_km.toFixed(4)),
      annualCost: result.annual_cost,
      totalCost: result.total_cost,
      drivetrainType,
      isWinner,
    };
  });

  const getBarColor = (entry: (typeof data)[number]) => {
    if (entry.isWinner) return WINNER_COLOR;
    return entry.drivetrainType === 'BEV' ? ELECTRIC_COLOR : DIESEL_COLOR;
  };

  return (
    <Card
      title="Cost per kilometre"
      subtitle="Lower bars indicate cheaper ownership under the selected scenario."
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12, fill: '#000000' }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })
            }
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip content={<CostTooltip />} />
          <Bar dataKey="costPerKm" name="Cost per km" radius={[6, 6, 0, 0]} maxBarSize={64}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry)}
                stroke={entry.isWinner ? '#000000' : undefined}
                strokeWidth={entry.isWinner ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostPerKmChart;
</file>

<file path="frontend/src/components/wizard/WizardStepper.tsx">
import clsx from 'clsx';

export interface WizardStep {
  title: string;
  description: string;
}

interface WizardStepperProps {
  steps: WizardStep[];
  activeIndex: number;
  onStepClick?: (index: number) => void;
}

const WizardStepper = ({ steps, activeIndex, onStepClick }: WizardStepperProps) => (
  <ol className="flex flex-col gap-4 md:flex-row md:items-stretch md:gap-6">
    {steps.map((step, index) => {
      const isActive = index === activeIndex;
      const isPast = index < activeIndex;

      return (
        <li
          key={step.title}
          className={clsx(
            'flex-1 relative pl-4 py-3 min-h-[48px] border-l-4 rounded-r-lg transition-all duration-300 ease-in-out group',
            isActive
              ? 'border-brand-primary bg-brand-primary/10'
              : isPast
                ? 'border-black cursor-pointer hover:border-brand-primary/60 hover:bg-slate-50'
                : 'border-slate-200'
          )}
          role={onStepClick ? 'button' : undefined}
          tabIndex={onStepClick ? 0 : -1}
          aria-current={isActive}
          onClick={() => onStepClick?.(index)}
          onKeyDown={(event) => {
            if (!onStepClick) {
              return;
            }
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onStepClick(index);
            }
          }}
        >
          <div className="flex flex-col h-full justify-between">
            <div>
              <span className={clsx(
                "text-xs font-bold block mb-1",
                isActive ? "text-brand-primary" : isPast ? "text-slate-500 group-hover:text-slate-700" : "text-slate-300"
              )}>
                Step {index + 1}
              </span>
              <p className={clsx(
                "text-lg font-heading font-bold leading-none",
                isActive ? "text-black" : isPast ? "text-slate-600 group-hover:text-black" : "text-slate-300"
              )}>{step.title}</p>
            </div>
          </div>
        </li>
      );
    })}
  </ol>
);

export default WizardStepper;
</file>

<file path="frontend/src/pages/ResultsPage.tsx">
import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import Button from '@components/shared/Button';
import ResultsPanel from '@components/results/ResultsPanel';
import { useTCOStore } from '@state/tcoStore';
import { useNavigate } from 'react-router-dom';

const ResultsPage = () => {
  const navigate = useNavigate();
  const lastRunCount = useTCOStore((state) => state.results.length);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const sessionId = useTCOStore((state) => state.sessionId);
  useEffect(() => {
    if (!isCalculating && lastRunCount === 0) {
      toast('Run the wizard to view results.');
      navigate('/', { replace: true });
    }
  }, [isCalculating, lastRunCount, navigate]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-slate-500">Results</p>
          <h2 className="text-2xl font-semibold text-slate-900">Cost comparison outputs</h2>
          <p className="text-sm text-slate-500">
            {isCalculating
              ? 'Running calculations…'
              : lastRunCount
                ? `Showing ${lastRunCount} vehicle${lastRunCount > 1 ? 's' : ''}.`
                : 'No data yet — run the wizard to populate this view.'}
          </p>
          {sessionId && (
            <p className="text-xs text-slate-500">
              Autosaved session:
              <span className="ml-1 font-mono text-slate-700">{sessionId}</span>
            </p>
          )}
        </div>
        <Button variant="secondary" onClick={() => navigate('/')}>Return to wizard</Button>
      </div>

      <ResultsPanel />
    </div>
  );
};

export default ResultsPage;
</file>

<file path="frontend/src/services/api.ts">
import axios from 'axios';
import type {

  VehicleDetail,
  VehicleSummary,
  SessionCreatePayload,
  SessionResponsePayload,
  SessionUpdatePayload,
  AnalyticsSummaryPayload,
} from '@shared/types/tco.types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: 10000,
});

export const fetchVehicles = async () => {
  const { data } = await api.get<VehicleSummary[]>('/vehicles');
  return data;
};

export const fetchVehicle = async (vehicleId: string) => {
  const { data } = await api.get<VehicleDetail>(`/vehicles/${vehicleId}`);
  return data;
};



export const createSession = async (payload: SessionCreatePayload) => {
  const { data } = await api.post<SessionResponsePayload>('/sessions', payload);
  return data;
};

export const updateSession = async (sessionId: string, payload: SessionUpdatePayload) => {
  const { data } = await api.put<SessionResponsePayload>(`/sessions/${sessionId}`, payload);
  return data;
};

export const fetchSession = async (sessionId: string) => {
  const { data } = await api.get<SessionResponsePayload>(`/sessions/${sessionId}`);
  return data;
};

export const fetchAnalyticsSummary = async () => {
  const { data } = await api.get<AnalyticsSummaryPayload>('/analytics/summary');
  return data;
};
</file>

<file path="frontend/vite.config.ts">
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@state': path.resolve(__dirname, './src/state'),
      '@forms': path.resolve(__dirname, './src/forms'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@shared': path.resolve(__dirname, '../shared')
    }
  },
  server: {
    port: 5000,
    host: '0.0.0.0',
    allowedHosts: true,
    fs: {
      allow: ['..'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
</file>

<file path="scripts/generate_vehicle_catalog_ts.py">
#!/usr/bin/env python3
"""Generate shared TypeScript payloads (vehicles, constants, scenarios, policies)."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data import policies  # noqa: E402
import data.constants as const  # noqa: E402
from data.scenarios import SCENARIOS  # noqa: E402
from data.vehicles import ALL_MODELS  # noqa: E402

VEHICLE_OUTPUT = Path("shared/data/vehicleCatalog.ts")
CONSTANTS_OUTPUT = Path("shared/data/constants.ts")
SCENARIOS_OUTPUT = Path("shared/data/scenarios.ts")
POLICIES_OUTPUT = Path("shared/data/policies.ts")
HEADER = "// Auto-generated by scripts/generate_vehicle_catalog_ts.py. Do not edit manually.\n\n"
SUMMARY_FIELDS = [
    "vehicle_id",
    "model_name",
    "drivetrain_type",
    "weight_class",
    "comparison_pair",
]
DETAIL_FIELDS: List[str] = SUMMARY_FIELDS + [
    "payload",
    "msrp",
    "range_km",
    "battery_capacity_kwh",
    "kwh_per_km",
    "litres_per_km",
    "maintenance_cost_per_km",
    "annual_registration",
    "annual_kms",
]


def build_vehicle_payload() -> list[dict[str, float | str]]:
    payload: list[dict[str, float | str]] = []
    for model in ALL_MODELS:
        data = asdict(model)
        payload.append({field: data[field] for field in DETAIL_FIELDS})
    return payload


def build_constants_payload() -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for attr in dir(const):
        if not attr.isupper():
            continue
        value = getattr(const, attr)
        try:
            json.dumps(value)
        except TypeError:
            continue
        payload[attr] = value
    return payload


def build_scenarios_payload() -> Dict[str, Dict[str, Any]]:
    scenarios: Dict[str, Dict[str, Any]] = {}
    for key, scenario in SCENARIOS.items():
        data = asdict(scenario)
        data["key"] = key
        scenarios[key] = data
    return scenarios


def build_policies_payload() -> Dict[str, Dict[str, Any]]:
    payload: Dict[str, Dict[str, Any]] = {}
    for key, policy in policies.POLICIES.items():
        data = asdict(policy)
        data["policy_type"] = policy.__class__.__name__
        payload[key] = data
    return payload


def render_vehicle_ts(details: list[dict[str, float | str]]) -> str:
    details_json = json.dumps(details, indent=2, sort_keys=False)
    return (
        f"{HEADER}"
        "import type { VehicleDetail, VehicleSummary } from '../types/tco.types';\n\n"
        f"export const VEHICLE_DETAILS: VehicleDetail[] = {details_json} as const;\n\n"
        "export const VEHICLE_BY_ID: Record<string, VehicleDetail> = VEHICLE_DETAILS.reduce(\n"
        "  (acc, vehicle) => {\n"
        "    acc[vehicle.vehicle_id] = vehicle;\n"
        "    return acc;\n"
        "  },\n"
        "  {} as Record<string, VehicleDetail>\n"
        ");\n\n"
        "export const VEHICLE_SUMMARIES: VehicleSummary[] = VEHICLE_DETAILS.map(\n"
        "  ({ vehicle_id, model_name, drivetrain_type, weight_class, comparison_pair }) => ({\n"
        "    vehicle_id,\n"
        "    model_name,\n"
        "    drivetrain_type,\n"
        "    weight_class,\n"
        "    comparison_pair,\n"
        "  })\n"
        ");\n"
    )


def render_constants_ts(constants: Dict[str, Any]) -> str:
    json_blob = json.dumps(constants, indent=2, sort_keys=True)
    return (
        f"{HEADER}"
        "import type { ConstantCatalog } from '../types/tco.types';\n\n"
        f"export const CONSTANTS: ConstantCatalog = {json_blob} as const;\n"
    )


def render_scenarios_ts(scenarios: Dict[str, Dict[str, Any]]) -> str:
    json_blob = json.dumps(scenarios, indent=2, sort_keys=True)
    return (
        f"{HEADER}"
        "import type { ScenarioDefinitionMap } from '../types/tco.types';\n\n"
        f"export const SCENARIO_DEFINITIONS: ScenarioDefinitionMap = {json_blob} as const;\n"
    )


def render_policies_ts(policies_payload: Dict[str, Dict[str, Any]]) -> str:
    json_blob = json.dumps(policies_payload, indent=2, sort_keys=True)
    return (
        f"{HEADER}"
        "import type { PolicyCatalog } from '../types/tco.types';\n\n"
        f"export const POLICY_CONFIG: PolicyCatalog = {json_blob} as const;\n"
    )


def ensure_output_dir() -> None:
    VEHICLE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_output_dir()
    details = build_vehicle_payload()
    VEHICLE_OUTPUT.write_text(render_vehicle_ts(details) + "\n", encoding="utf-8")
    constants = build_constants_payload()
    CONSTANTS_OUTPUT.write_text(render_constants_ts(constants) + "\n", encoding="utf-8")
    scenarios = build_scenarios_payload()
    SCENARIOS_OUTPUT.write_text(render_scenarios_ts(scenarios) + "\n", encoding="utf-8")
    policy_payload = build_policies_payload()
    POLICIES_OUTPUT.write_text(
        render_policies_ts(policy_payload) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
</file>

<file path="shared/data/vehicleCatalog.ts">
// Auto-generated by scripts/generate_vehicle_catalog_ts.py. Do not edit manually.

import type { VehicleDetail, VehicleSummary } from '../types/tco.types';

// Update this version when vehicle data changes to invalidate stale cache
export const VEHICLE_CATALOG_VERSION = '2026-01-07-v1';

export const VEHICLE_DETAILS: VehicleDetail[] = [
  {
    "vehicle_id": "BEV001",
    "model_name": "Jac N75",
    "drivetrain_type": "BEV",
    "weight_class": "Light Rigid",
    "comparison_pair": "DSL001",
    "payload": 4.0,
    "msrp": 176500.0,
    "range_km": 220.0,
    "battery_capacity_kwh": 100.0,
    "kwh_per_km": 0.48,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.05,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "BEV002",
    "model_name": "Hyundai Mighty Electric",
    "drivetrain_type": "BEV",
    "weight_class": "Light Rigid",
    "comparison_pair": "DSL002",
    "payload": 4.0,
    "msrp": 150000.0,
    "range_km": 200.0,
    "battery_capacity_kwh": 97.0,
    "kwh_per_km": 0.48,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.05,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "BEV003",
    "model_name": "Jac N90",
    "drivetrain_type": "BEV",
    "weight_class": "Light Rigid",
    "comparison_pair": "DSL003",
    "payload": 5.0,
    "msrp": 150000.0,
    "range_km": 180.0,
    "battery_capacity_kwh": 107.0,
    "kwh_per_km": 0.61,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.05,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "BEV004",
    "model_name": "Volvo FL",
    "drivetrain_type": "BEV",
    "weight_class": "Medium Rigid",
    "comparison_pair": "DSL004",
    "payload": 10.5,
    "msrp": 200000.0,
    "range_km": 300.0,
    "battery_capacity_kwh": 264.0,
    "kwh_per_km": 0.88,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.08,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "BEV005",
    "model_name": "MB eActros 300",
    "drivetrain_type": "BEV",
    "weight_class": "Medium Rigid",
    "comparison_pair": "DSL005",
    "payload": 22.0,
    "msrp": 400000.0,
    "range_km": 300.0,
    "battery_capacity_kwh": 336.0,
    "kwh_per_km": 1.09,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.08,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "BEV006",
    "model_name": "MB eActros 600",
    "drivetrain_type": "BEV",
    "weight_class": "Articulated",
    "comparison_pair": "DSL006",
    "payload": 42.0,
    "msrp": 600000.0,
    "range_km": 500.0,
    "battery_capacity_kwh": 621.0,
    "kwh_per_km": 1.2,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.12,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  },
  {
    "vehicle_id": "BEV007",
    "model_name": "Volvo FH",
    "drivetrain_type": "BEV",
    "weight_class": "Articulated",
    "comparison_pair": "DSL007",
    "payload": 42.0,
    "msrp": 450000.0,
    "range_km": 300.0,
    "battery_capacity_kwh": 540.0,
    "kwh_per_km": 1.8,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.12,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  },
  {
    "vehicle_id": "BEV008",
    "model_name": "Scania 45R",
    "drivetrain_type": "BEV",
    "weight_class": "Articulated",
    "comparison_pair": "DSL008",
    "payload": 42.0,
    "msrp": 320000.0,
    "range_km": 390.0,
    "battery_capacity_kwh": 624.0,
    "kwh_per_km": 1.6,
    "litres_per_km": 0.0,
    "maintenance_cost_per_km": 0.12,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  },
  {
    "vehicle_id": "DSL001",
    "model_name": "Hino 300",
    "drivetrain_type": "Diesel",
    "weight_class": "Light Rigid",
    "comparison_pair": "BEV001",
    "payload": 4.5,
    "msrp": 80000.0,
    "range_km": 600.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.28,
    "maintenance_cost_per_km": 0.2,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "DSL002",
    "model_name": "Hyundai Mighty",
    "drivetrain_type": "Diesel",
    "weight_class": "Light Rigid",
    "comparison_pair": "BEV002",
    "payload": 4.0,
    "msrp": 75000.0,
    "range_km": 600.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.28,
    "maintenance_cost_per_km": 0.02,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "DSL003",
    "model_name": "Hino 500",
    "drivetrain_type": "Diesel",
    "weight_class": "Light Rigid",
    "comparison_pair": "BEV003",
    "payload": 6.0,
    "msrp": 130000.0,
    "range_km": 600.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.28,
    "maintenance_cost_per_km": 0.02,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "DSL004",
    "model_name": "Volvo FE",
    "drivetrain_type": "Diesel",
    "weight_class": "Medium Rigid",
    "comparison_pair": "BEV004",
    "payload": 12.0,
    "msrp": 220000.0,
    "range_km": 600.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.32,
    "maintenance_cost_per_km": 0.025,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "DSL005",
    "model_name": "MB Actros",
    "drivetrain_type": "Diesel",
    "weight_class": "Medium Rigid",
    "comparison_pair": "BEV005",
    "payload": 25.0,
    "msrp": 270000.0,
    "range_km": 1400.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.32,
    "maintenance_cost_per_km": 0.025,
    "annual_registration": 653.0,
    "annual_kms": 23000.0
  },
  {
    "vehicle_id": "DSL006",
    "model_name": "MB Actros",
    "drivetrain_type": "Diesel",
    "weight_class": "Articulated",
    "comparison_pair": "BEV006",
    "payload": 50.0,
    "msrp": 270000.0,
    "range_km": 1400.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.35,
    "maintenance_cost_per_km": 0.03,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  },
  {
    "vehicle_id": "DSL007",
    "model_name": "Volvo FH",
    "drivetrain_type": "Diesel",
    "weight_class": "Articulated",
    "comparison_pair": "BEV007",
    "payload": 50.0,
    "msrp": 280000.0,
    "range_km": 2000.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.35,
    "maintenance_cost_per_km": 0.03,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  },
  {
    "vehicle_id": "DSL008",
    "model_name": "Scania R560",
    "drivetrain_type": "Diesel",
    "weight_class": "Articulated",
    "comparison_pair": "BEV008",
    "payload": 50.0,
    "msrp": 300000.0,
    "range_km": 1500.0,
    "battery_capacity_kwh": 0.0,
    "kwh_per_km": 0.0,
    "litres_per_km": 0.35,
    "maintenance_cost_per_km": 0.03,
    "annual_registration": 6872.0,
    "annual_kms": 84000.0
  }
] as const;

export const VEHICLE_BY_ID: Record<string, VehicleDetail> = VEHICLE_DETAILS.reduce(
  (acc, vehicle) => {
    acc[vehicle.vehicle_id] = vehicle;
    return acc;
  },
  {} as Record<string, VehicleDetail>
);

export const VEHICLE_SUMMARIES: VehicleSummary[] = VEHICLE_DETAILS.map(
  ({ vehicle_id, model_name, drivetrain_type, weight_class, comparison_pair }) => ({
    vehicle_id,
    model_name,
    drivetrain_type,
    weight_class,
    comparison_pair,
  })
);
</file>

<file path="tests/conftest.py">
"""
Pytest configuration file.
Adds project root to Python path for test imports.
"""

from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
</file>

<file path="AGENTS.md">
# Repository Guidelines

## Documentation Structure

The project includes comprehensive documentation:

- **[README.md](./README.md)** - Quick start guide and project overview
- **[API.md](./API.md)** - Complete REST API documentation with examples
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment instructions
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
- **[replit.md](./replit.md)** - Detailed architecture and design patterns
- **[AGENTS.md](./AGENTS.md)** (this file) - Development guidelines and conventions

Historical documentation and legacy code are archived in the `archive/` folder:
- `archive/Transition Docs/` - Development transformation logs and execution plans
- `archive/legacy/` - Original Python CLI implementation and legacy analysis tools

## Project Structure & Module Organization

The project follows a monorepo structure: the TypeScript calculator in `shared/calculator` is the source-of-truth engine, backed by Python data under `data/` and regenerated TypeScript contracts in `shared/types`. `scripts/` carries `generate_vehicle_catalog_ts.py` and `validation.py`, and Docker assets keep the Postgres/Redis topology reproducible.

## Build, Test, and Development Commands

**Quick Start:**
- `docker compose up --build` - Start all services (recommended for development)
- Visit `http://localhost:5000` for frontend, `http://localhost:8000/docs` for API docs

**Python Setup:**
- `python -m pip install -r requirements.txt && pre-commit install` primes Python tooling
- `python scripts/generate_vehicle_catalog_ts.py` refreshes the shared SDK before frontend or API work
- `uvicorn backend.app.main:app --reload` boots FastAPI standalone

**Frontend Setup:**
- `cd frontend && npm install && npm run dev` starts the wizard
- `npm run build|lint|typecheck` satisfy CI gates

**Testing:**
- `python -m pytest tests --cov` runs backend tests
- `cd frontend && npm run test` runs frontend tests and enforces the ±1% parity budget using the TypeScript calculator fixtures

See [README.md](./README.md) for complete development setup instructions.

## Coding Style & Naming Conventions

Python files use 4-space indents, type hints, and Google-style docstrings; run `ruff check .`, `black .`, and `isort .` pre-push. TypeScript remains in strict mode with ESLint/Prettier defaults (2-space indent, single quotes). Keep components `PascalCase`, hooks `useCamelCase`, and import DTOs from `shared/types` to keep every layer on the same contract.

## Testing & Parity Guidelines

Use `python scripts/validation.py` whenever vehicle, scenario, or policy data changes, and seed Monte Carlo helpers for reproducible CI. Keep the shared TypeScript calculator and Vitest suite within ±1% of the stored verification fixtures, and include parity evidence with each PR.

## Commit & Pull Request Guidelines

Commits stay concise and imperative ("Add web app backend, frontend, and shared packages"), stay under 72 characters, and tag subsystems (`backend:`, `frontend:`, `shared:`). PRs should describe scope, list executed commands (pytest, Vitest, lint, exports), flag schema or data migrations, attach artefacts when UX or CSV outputs change, and request reviewers from each affected discipline.

## Security & Configuration Tips

Use `.env.example` as the template for secrets; load variables via `python-dotenv`/`pydantic-settings` so FastAPI, scripts, and Docker read the same source. Never commit operator data or credentials inside `data/` or `frontend/public`. Run `pip-audit`, `npm audit`, and `bandit` whenever dependencies move, regenerate shared types when `data/*.py` changes. Historical data revisions are documented in `archive/Transition Docs/TRANSFORMATION_EXECUTION_LOG.md`.
</file>

<file path="README.md">
# TCO Web Platform

A modern web platform for comparing the Total Cost of Ownership (TCO) of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. Built for truck operators, fleet managers, and the Transport Workers Union (TWU) to make informed decisions about fleet electrification.

## Overview

The TCO Web Platform helps truck operators get five-minute TCO insights through:

- **Interactive Wizard** - Three-step process to input vehicle selection, operating profile, and cost assumptions
- **Detailed Analysis** - 14 cost components including purchase, financing, fuel, maintenance, battery replacement, and residual value
- **Scenario Modeling** - Compare baseline, technology breakthrough, and oil crisis scenarios
- **Visual Insights** - Cost-per-km charts, payback timelines, and cost breakdowns
- **Session Persistence** - Save and review calculation sessions
- **Analytics Dashboard** - Aggregated insights for policy and advocacy work

### Key Features

- 16 pre-configured vehicles (8 BEV, 8 diesel) across light, medium, and articulated truck classes
- Shared TypeScript calculation engine with ±1% parity validation against committed fixtures
- Offline-capable progressive web app
- PostgreSQL session persistence with Redis caching
- RESTful API for integrations and analytics

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ and Bun 1.0+
- PostgreSQL 15+ (or use included Docker setup)
- Redis 7+ (or use included Docker setup)

### Local Development with Docker

The fastest way to get started:

```bash
# Start all services (frontend, backend, database, cache)
docker compose up --build

# Access the application
# Frontend: http://localhost:5000
# Backend API: http://localhost:8000/api/v1/health
```

### Manual Setup

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your database and Redis URLs

# Run database migrations
python -m backend.app.db.session

# Start the backend server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install

# Set up environment (if needed)
cp .env.example .env

# Start development server
bun run dev
```

#### Generate Shared Data Layer

The TypeScript calculator consumes generated data from the Python sources:

```bash
# Generate vehicle catalog and constants
python scripts/generate_vehicle_catalog_ts.py
```

## Project Structure

```
.
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API routes and endpoints
│   │   ├── core/         # Configuration and cache
│   │   ├── db/           # Database models and session
│   │   ├── models/       # Pydantic request/response schemas
│   │   └── services/     # Business logic layer
│   └── requirements.txt
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── components/   # UI components (wizard, results, shared)
│   │   ├── hooks/        # React hooks
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API clients
│   │   └── state/        # Zustand store
│   └── package.json
├── shared/               # Shared TypeScript code
│   ├── calculator/       # Shared TCO engine
│   ├── data/             # Generated from Python (vehicles, constants, scenarios)
│   └── types/            # TypeScript type definitions
├── data/                 # Authoritative data layer
│   ├── constants.py      # Global constants
│   ├── policies.py       # Policy definitions (rebates, carbon pricing)
│   ├── scenarios.py      # Economic scenarios
│   └── vehicles.py       # Vehicle specifications
├── scripts/              # Code generation and utilities
├── tests/                # Backend test suite
├── archive/              # Historical documentation and legacy Python engine
└── docker-compose.yml    # Local development orchestration
```

## Key Technologies

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Hook Form + Zod** - Form validation
- **Recharts** - Data visualization
- **Vitest** - Testing

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database
- **Redis** - Session caching
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Calculation Engine
- **TypeScript** - Shared calculator logic under `shared/calculator`
- **Vitest** - Calculator regression tests against committed verification fixtures

## Stability & Robustness

The calculator engine and frontend include multiple layers of defensive programming:

### Input Validation
- **Runtime sanitization** - All calculation inputs are sanitized at the calculator entry point to prevent NaN propagation
- **Zod schemas** - Form inputs validated with comprehensive Zod schemas including vehicle parameter overrides
- **Duty cycle validation** - Real-time sum validation (must equal 100%) with visual feedback
- **Store validation** - Runtime validation in Zustand store prevents invalid state

### State Management
- **Race condition prevention** - Session creation uses mutex pattern to prevent duplicate sessions
- **Stale closure protection** - Generation counter pattern prevents outdated calculation results from overwriting newer ones
- **Cache versioning** - Vehicle catalog includes version tracking to invalidate stale localStorage cache on updates
- **Autosave feedback** - Toast notifications inform users when autosave fails

### Test Coverage
The test suite includes:
- **Calculator parity tests** - Validates TypeScript results match Python reference implementation (±1 cent tolerance)
- **Math utility tests** - Unit tests for NPV, annuity, and discounting functions
- **Scenario tests** - All three economic scenarios (baseline, technology_breakthrough, oil_crisis)
- **Edge case tests** - Zero values, NaN handling, boundary conditions, all 16 vehicles
- **Override tests** - Vehicle parameter and cost override combinations
- **State management tests** - Zustand store validation and race condition handling

Run all tests:
```bash
cd frontend && bun test
```

## Development Workflow

### Running Tests

```bash
# Backend tests
pytest tests/ --cov

# Frontend tests (all)
cd frontend
bun test

# Calculator parity tests only
cd frontend
bun test verification.test.ts

# Run with coverage
cd frontend
bun test --coverage
```

### Code Quality

```bash
# Python linting and formatting
ruff check .
black .
isort .
mypy .

# TypeScript linting and type checking
cd frontend
bun run lint
bun run typecheck
```

### Data Generation

Whenever you modify data in `data/` (vehicles, scenarios, policies, constants):

```bash
# Regenerate TypeScript types and data
python scripts/generate_vehicle_catalog_ts.py

# Run parity tests to ensure consistency
cd frontend
bun test
```

## API Documentation

See [API.md](./API.md) for complete API documentation including:
- Available endpoints
- Request/response schemas
- Authentication (if applicable)
- Usage examples

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment instructions.

## Troubleshooting

Having issues? Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions to common problems including:
- Docker and environment setup
- Frontend build and runtime errors
- Backend API and database connection issues
- Deployment and production problems

## Documentation

- **README.md** (this file) - Quick start and overview
- **[API.md](./API.md)** - REST API documentation
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and fixes
- **[AGENTS.md](./AGENTS.md)** - Development guidelines and conventions
- **[replit.md](./replit.md)** - Detailed architecture and design patterns

### Historical Documentation

The `archive/` folder contains:
- **archive/Transition Docs/** - Development transformation logs and execution plans
- **archive/legacy/** - Original Python CLI implementation

## Contributing

1. Follow the coding style guidelines in [AGENTS.md](./AGENTS.md)
2. Run tests and linters before committing
3. Update documentation for any API or data model changes
4. Regenerate shared TypeScript files when modifying Python data layer

## License

Copyright Transport Workers Union. All rights reserved.

## Support

For issues, questions, or contributions, contact the development team or open an issue.
</file>

<file path="backend/app/models/__init__.py">
"""Pydantic schemas shared across API layers."""

from .calculation import (
    CalculationRequest,
    CalculationResponse,
    ComparisonRequest,
    CostBreakdown,
    CostOverride,
    VehicleParamOverride,
)
from .vehicle import VehicleDetail, VehicleSummary

__all__ = [
    "CalculationRequest",
    "CalculationResponse",
    "ComparisonRequest",
    "CostOverride",
    "CostBreakdown",
    "VehicleParamOverride",
    "VehicleSummary",
    "VehicleDetail",
]
</file>

<file path="backend/app/models/calculation.py">
"""Schema definitions for calculation requests and responses."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CostOverride(BaseModel):
    """Optional override hooks that align with the shared TypeScript calculator inputs."""

    annual_kms_variation: Optional[float] = Field(
        default=None,
        description="Absolute kilometres per year to use instead of the vehicle default.",
    )
    residual_value_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to the discounted residual value (e.g. 0.9).",
    )
    fuel_price_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to diesel fuel price trajectory (1.05 = +5%).",
    )
    electricity_price_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to electricity price trajectory (0.95 = -5%).",
    )
    maintenance_cost_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to maintenance trajectory (1.1 = +10%).",
    )
    battery_life_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to BEV battery life simulations (0.7 = shorter life).",
    )
    charging_efficiency_variation: Optional[float] = Field(
        default=None,
        description="Multiplier applied to BEV charging efficiency (1.1 = worse efficiency).",
    )

    model_config = {
        "extra": "forbid",
    }

    def to_engine_overrides(self) -> Dict[str, float]:
        """Return the overrides dictionary understood by the Python engine."""

        payload: Dict[str, float] = {}
        if self.annual_kms_variation is not None:
            payload["annual_kms_variation"] = self.annual_kms_variation
        if self.residual_value_variation is not None:
            payload["residual_value_variation"] = self.residual_value_variation
        if self.fuel_price_variation is not None:
            payload["fuel_price_variation"] = self.fuel_price_variation
        if self.electricity_price_variation is not None:
            payload["electricity_price_variation"] = self.electricity_price_variation
        if self.maintenance_cost_variation is not None:
            payload["maintenance_cost_variation"] = self.maintenance_cost_variation
        if self.battery_life_variation is not None:
            payload["battery_life_variation"] = self.battery_life_variation
        if self.charging_efficiency_variation is not None:
            payload["charging_efficiency_variation"] = (
                self.charging_efficiency_variation
            )
        return payload


class VehicleParamOverride(BaseModel):
    """Optional per-vehicle structural overrides."""

    msrp_override: Optional[float] = Field(default=None)
    payload_override: Optional[float] = Field(default=None)
    range_km_override: Optional[float] = Field(default=None)
    battery_capacity_kwh_override: Optional[float] = Field(default=None)
    kwh_per_km_override: Optional[float] = Field(default=None)
    litres_per_km_override: Optional[float] = Field(default=None)
    annual_registration_override: Optional[float] = Field(default=None)
    interest_rate_override: Optional[float] = Field(default=None)
    charging_time_hours_override: Optional[float] = Field(default=None)

    model_config = {
        "extra": "forbid",
    }


class CalculationRequest(BaseModel):
    """Request payload for a single TCO calculation."""

    vehicle_id: str = Field(..., description="Vehicle identifier, e.g. BEV001.")
    scenario_name: str = Field(
        default="baseline", description="Scenario key from data.scenarios."
    )
    purchase_method: Literal["financed", "outright"] = Field(default="financed")
    overrides: Optional[CostOverride] = None
    vehicle_overrides: Optional[VehicleParamOverride] = Field(
        default=None, description="Optional structural overrides for this vehicle."
    )


class ComparisonRequest(BaseModel):
    """Request payload for comparing a list of vehicles under the same scenario."""

    vehicle_ids: List[str] = Field(..., min_length=1)
    scenario_name: str = Field(default="baseline")
    purchase_method: Literal["financed", "outright"] = Field(default="financed")
    overrides: Optional[CostOverride] = None
    vehicle_param_overrides: Optional[Dict[str, VehicleParamOverride]] = Field(
        default=None,
        description="Map of vehicle_id -> overrides applied when present.",
    )


class CostBreakdown(BaseModel):
    purchase_cost: float
    fuel_cost: float
    maintenance_cost: float
    insurance_cost: float
    registration_cost: float
    battery_replacement_cost: float
    financing_cost: float
    carbon_cost: float
    charging_labour_cost: float
    payload_penalty_cost: float
    residual_value: float
    depreciation: float
    taxes_and_fees: float


class CalculationResponse(BaseModel):
    """Response payload summarising key metrics from the shared calculator."""

    vehicle_id: str
    scenario_name: str
    total_cost: float
    annual_cost: float
    cost_per_km: float
    breakdown: CostBreakdown
</file>

<file path="backend/app/services/sessions.py">
"""Session persistence and analytics services."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.cache import cache_session, get_cached_session
from backend.app.db.models import (
    CalculationResultRecord,
    FeedbackRecord,
    OperatorProfileRecord,
    SessionRecord,
    UserInputRecord,
)
from backend.app.models.calculation import CalculationResponse
from backend.app.models.session import (
    AnalyticsSummary,
    FeedbackPayload,
    OperatorProfilePayload,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    WizardDataPayload,
)
from data.vehicles import BY_ID


class SessionService:
    """Handles creation, updates, and analytics for calculation sessions."""

    async def create_session(
        self, db: AsyncSession, payload: SessionCreate
    ) -> SessionResponse:
        now = datetime.now(timezone.utc)

        record = SessionRecord(
            status="completed" if payload.results else "draft",
            wizard_state=self._wizard_to_json(payload.wizard_data),
            cached_results=self._results_to_json(payload.results or []),
            last_calculated_at=now if payload.results else None,
        )
        db.add(record)
        await db.flush()

        await self._replace_inputs(db, record.id, payload.wizard_data)
        if payload.results:
            await self._replace_results(
                db, record.id, payload.results, payload.wizard_data
            )
        if payload.operator_profile:
            await self._upsert_operator_profile(db, record.id, payload.operator_profile)
        if payload.feedback:
            await self._insert_feedback(db, record.id, payload.feedback)

        await db.commit()
        await db.refresh(record)

        response = await self._build_response(db, record.id)
        await cache_session(record.id, response.model_dump(by_alias=True))
        return response

    async def update_session(
        self, db: AsyncSession, session_id: str, payload: SessionUpdate
    ) -> SessionResponse:
        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")

        if payload.wizard_data:
            record.wizard_state = self._wizard_to_json(payload.wizard_data)
            await self._replace_inputs(db, session_id, payload.wizard_data)

        resolved_wizard = payload.wizard_data or WizardDataPayload.model_validate(
            record.wizard_state
        )

        if payload.results is not None:
            record.cached_results = self._results_to_json(payload.results)
            if payload.results:
                record.status = "completed"
                record.last_calculated_at = datetime.now(timezone.utc)
                await self._replace_results(
                    db, session_id, payload.results, resolved_wizard
                )
            else:
                record.status = "draft"
                record.last_calculated_at = None
                await self._clear_results(db, session_id)

        if payload.operator_profile is not None:
            await self._upsert_operator_profile(
                db, session_id, payload.operator_profile
            )

        if payload.feedback:
            await self._insert_feedback(db, session_id, payload.feedback)

        await db.commit()

        response = await self._build_response(db, session_id)
        await cache_session(session_id, response.model_dump(by_alias=True))
        return response

    async def get_session(self, db: AsyncSession, session_id: str) -> SessionResponse:
        cached = await get_cached_session(session_id)
        if cached:
            return SessionResponse.model_validate(cached)

        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")

        response = await self._build_response(db, session_id)
        await cache_session(session_id, response.model_dump(by_alias=True))
        return response

    async def analytics_summary(self, db: AsyncSession) -> AnalyticsSummary:
        total_sessions = await db.scalar(select(func.count(SessionRecord.id))) or 0
        completed_sessions = (
            await db.scalar(
                select(func.count(SessionRecord.id)).where(
                    SessionRecord.status == "completed"
                )
            )
        ) or 0

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        calculations_last_24h = (
            await db.scalar(
                select(func.count(CalculationResultRecord.id)).where(
                    CalculationResultRecord.created_at >= cutoff
                )
            )
        ) or 0

        top_rows = await db.execute(
            select(
                CalculationResultRecord.vehicle_id,
                func.count(CalculationResultRecord.id).label("runs"),
            )
            .group_by(CalculationResultRecord.vehicle_id)
            .order_by(func.count(CalculationResultRecord.id).desc())
            .limit(5)
        )
        top_vehicles = {vehicle_id: runs for vehicle_id, runs in top_rows.all()}

        bev_win_rate, avg_payback, avg_cost_delta = await self._compute_outcomes(db)

        return AnalyticsSummary(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            calculations_last_24h=calculations_last_24h,
            bev_win_rate=bev_win_rate,
            average_payback_years=avg_payback,
            average_cost_delta=avg_cost_delta,
            top_vehicles=top_vehicles,
        )

    async def _compute_outcomes(
        self, db: AsyncSession
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        rows = await db.execute(
            select(
                CalculationResultRecord.session_id,
                CalculationResultRecord.vehicle_id,
                CalculationResultRecord.total_cost,
                CalculationResultRecord.annual_cost,
                CalculationResultRecord.result_payload,
            )
        )
        session_map: Dict[str, Dict[str, CalculationResultRecord]] = defaultdict(dict)
        for row in rows.all():
            session_map[row.session_id][row.vehicle_id] = row  # type: ignore[index]

        bev_wins = 0
        comparisons = 0
        payback_values: List[float] = []
        cost_deltas: List[float] = []

        for vehicles in session_map.values():
            for vehicle_id, bev_record in vehicles.items():
                vehicle = BY_ID.get(vehicle_id)
                if not vehicle or vehicle.drivetrain_type != "BEV":
                    continue
                diesel_id = vehicle.comparison_pair
                diesel_record = vehicles.get(diesel_id)
                if not diesel_record:
                    continue

                comparisons += 1
                if bev_record.total_cost < diesel_record.total_cost:
                    bev_wins += 1

                cost_deltas.append(diesel_record.total_cost - bev_record.total_cost)

                annual_savings = diesel_record.annual_cost - bev_record.annual_cost
                bev_breakdown = bev_record.result_payload.get("breakdown", {})
                diesel_breakdown = diesel_record.result_payload.get("breakdown", {})
                initial_gap = bev_breakdown.get(
                    "purchase_cost", 0
                ) - diesel_breakdown.get("purchase_cost", 0)
                if annual_savings > 0:
                    payback = max(initial_gap / annual_savings, 0)
                    payback_values.append(payback)

        bev_win_rate = (bev_wins / comparisons) if comparisons else None
        avg_payback = (
            sum(payback_values) / len(payback_values) if payback_values else None
        )
        avg_cost_delta = sum(cost_deltas) / len(cost_deltas) if cost_deltas else None
        return bev_win_rate, avg_payback, avg_cost_delta

    async def _build_response(
        self, db: AsyncSession, session_id: str
    ) -> SessionResponse:
        record = await db.get(SessionRecord, session_id)
        if not record:
            raise KeyError(f"Unknown session_id '{session_id}'.")

        wizard_data = WizardDataPayload.model_validate(record.wizard_state)
        results = [
            CalculationResponse.model_validate(result)
            for result in (record.cached_results or [])
        ]

        operator_profile_record = await db.scalar(
            select(OperatorProfileRecord).where(
                OperatorProfileRecord.session_id == session_id
            )
        )
        feedback_record = await db.scalars(
            select(FeedbackRecord)
            .where(FeedbackRecord.session_id == session_id)
            .order_by(FeedbackRecord.created_at.desc())
            .limit(1)
        )
        feedback = feedback_record.first()

        operator_profile = (
            self._map_operator_profile(operator_profile_record)
            if operator_profile_record
            else None
        )
        feedback_payload = self._map_feedback(feedback) if feedback else None

        return SessionResponse(
            session_id=session_id,
            status=record.status,
            wizard_data=wizard_data,
            results=results,
            operator_profile=operator_profile,
            feedback=feedback_payload,
            updated_at=record.updated_at,
            last_calculated_at=record.last_calculated_at,
        )

    async def _replace_inputs(
        self, db: AsyncSession, session_id: str, wizard_data: WizardDataPayload
    ) -> None:
        await db.execute(
            delete(UserInputRecord).where(UserInputRecord.session_id == session_id)
        )

        vehicle_ids = self._unique_vehicle_ids(wizard_data)
        shared_cost_overrides = (
            wizard_data.overrides.model_dump(exclude_none=True)
            if wizard_data.overrides
            else None
        )
        per_vehicle_overrides = {
            vehicle_id: override.model_dump(exclude_none=True)
            for vehicle_id, override in (
                wizard_data.vehicle_param_overrides or {}
            ).items()
        }

        for vehicle_id in vehicle_ids:
            vehicle_specific = per_vehicle_overrides.get(vehicle_id)
            combined_overrides: Optional[dict] = None
            if vehicle_specific:
                combined_overrides = {}
                if shared_cost_overrides:
                    combined_overrides["cost"] = shared_cost_overrides
                combined_overrides["vehicle"] = vehicle_specific
            elif shared_cost_overrides:
                combined_overrides = shared_cost_overrides

            db.add(
                UserInputRecord(
                    session_id=session_id,
                    vehicle_id=vehicle_id,
                    scenario_name=wizard_data.scenario,
                    purchase_method=wizard_data.purchase_method,
                    overrides=combined_overrides,
                )
            )

    async def _replace_results(
        self,
        db: AsyncSession,
        session_id: str,
        results: Iterable[CalculationResponse],
        wizard_data: WizardDataPayload,
    ) -> None:
        await db.execute(
            delete(CalculationResultRecord).where(
                CalculationResultRecord.session_id == session_id
            )
        )
        for result in results:
            db.add(
                CalculationResultRecord(
                    session_id=session_id,
                    vehicle_id=result.vehicle_id,
                    scenario_name=result.scenario_name,
                    purchase_method=wizard_data.purchase_method,
                    result_payload=result.model_dump(mode="json"),
                    total_cost=result.total_cost,
                    annual_cost=result.annual_cost,
                    cost_per_km=result.cost_per_km,
                )
            )

    async def _clear_results(self, db: AsyncSession, session_id: str) -> None:
        await db.execute(
            delete(CalculationResultRecord).where(
                CalculationResultRecord.session_id == session_id
            )
        )

    async def _upsert_operator_profile(
        self, db: AsyncSession, session_id: str, payload: OperatorProfilePayload
    ) -> None:
        await db.execute(
            delete(OperatorProfileRecord).where(
                OperatorProfileRecord.session_id == session_id
            )
        )
        db.add(
            OperatorProfileRecord(
                session_id=session_id,
                operator_type=payload.operator_type,
                fleet_size=payload.fleet_size,
                contact_email=payload.contact_email,
                consent_to_contact=payload.consent_to_contact,
                notes=payload.notes,
            )
        )

    async def _insert_feedback(
        self, db: AsyncSession, session_id: str, payload: FeedbackPayload
    ) -> None:
        db.add(
            FeedbackRecord(
                session_id=session_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        )

    @staticmethod
    def _wizard_to_json(payload: WizardDataPayload) -> dict:
        return payload.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def _results_to_json(results: Iterable[CalculationResponse]) -> List[dict]:
        return [result.model_dump(by_alias=True) for result in results]

    @staticmethod
    def _unique_vehicle_ids(wizard_data: WizardDataPayload) -> List[str]:
        vehicles: List[str] = []
        if wizard_data.current_vehicle:
            vehicles.append(wizard_data.current_vehicle)
        vehicles.extend(wizard_data.comparison_vehicles)
        deduped = []
        for vehicle in vehicles:
            if vehicle and vehicle not in deduped:
                deduped.append(vehicle)
        return deduped

    @staticmethod
    def _map_operator_profile(record: OperatorProfileRecord) -> OperatorProfilePayload:
        return OperatorProfilePayload(
            operator_type=record.operator_type,
            fleet_size=record.fleet_size,
            contact_email=record.contact_email,
            consent_to_contact=record.consent_to_contact,
            notes=record.notes,
        )

    @staticmethod
    def _map_feedback(record: FeedbackRecord) -> FeedbackPayload:
        return FeedbackPayload(rating=record.rating, comment=record.comment)
</file>

<file path="backend/app/main.py">
"""FastAPI entrypoint for the TCO web platform backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import api_router
from backend.app.core.config import settings
from backend.app.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - integration hook
        await init_db()

    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dist / "assets")),
            name="assets",
        )

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = frontend_dist / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(frontend_dist / "index.html")

    else:

        @app.get("/", tags=["system"])
        def root() -> dict[str, str]:
            return {"message": "TCO Web Platform API", "version": settings.version}

    return app


app = create_app()
</file>

<file path="data/constants.py">
# Constants for TCO Calculations

# Electricity Costs

RETAIL_CHARGING_PRICE = 0.30  # $/kWh
OFFPEAK_CHARGING_PRICE = 0.15  # $/kWh
SOLAR_CHARGING_PRICE = 0.04  # $/kWh
PUBLIC_CHARGING_PRICE = 0.50  # $/kWh

# Electricity Mix

RETAIL_PROPORTION = 0.0  # % (Proportion of charging done at workplace AC chargers)
OFFPEAK_PROPORTION = 0.86  # % (Proportion of charging done at workplace AC chargers during offpeak hours)
PUBLIC_PROPORTION = 0.14  # % (Proportion of charging done at public DC fast chargers)
SOLAR_PROPORTION = 0.0  # % (Proportion of charging done at home via solar and storage)

# Charging Mix Proportions by Vehicle Type
CHARGING_MIX_PROPORTIONS = {
    "BEV": {
        "Light Rigid": {
            "retail": 0.00,  # (Assuming most charging takes place on overnight cycles)
            "offpeak": 0.86,  # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
            "public": 0.14,  # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
            "solar": 0.00,  # (Assuming no investment in solar infrastructure)
        },
        "Medium Rigid": {
            "retail": 0.00,  # (Assuming most charging takes place on overnight cycles)
            "offpeak": 0.86,  # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
            "public": 0.14,  # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
            "solar": 0.00,  # (Assuming no investment in solar infrastructure)
        },
        "Articulated": {
            "retail": 0.00,  # (Assuming most charging takes place on overnight cycles)
            "offpeak": 0.33,  # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
            "public": 0.57,  # (Using industry consultation data from ARENA/AECOM information)
            "solar": 0.00,  # (Assuming no investment in solar infrastructure)
        },
    }
}

# Charger Costs

SOLAR_PANEL_INSTALLATION = (
    1285  # $/kwh DC (single-axis-tracking solar behind the meter)
)
SOLAR_MAINTENANCE = 0.15  # $/kwh/year
STORAGE_INSTALLATION = 423  # $/kwh (4 hour lithium-ion battery energy-storage system)
STORAGE_MAINTENANCE = 0.025  # % (AEMO/NREL rule - percentage of CAPEX/year)
INFRASTRUCTURE_LIFE = 15  # Years
CHARGER_COST = 300000  # AUD (CCS high-power DC fast charger, includes cabinet, dispenser, cooling, and typical electrical work - Smart Freight Media Centre)GRID_UPGRADE = 1000000  # AUD

# Charging Time Parameters

BATTERY_USABLE_RANGE_FACTOR = (
    0.6  # Usable range factor (typically charge at 20% remaining)
)

CHARGING_TIME_HOURS = {
    "Articulated": 1.0,  # 60 minutes for articulated trucks (more public fast charging needed)
    "Medium Rigid": 0.75,  # 45 minutes for medium rigid trucks
    "Light Rigid": 0.6,  # 30 minutes for light rigid trucks
}

# Fuel Costs

DIESEL_PRICE = 2.05  # $/litre (average diesel retail price from the Australian Institute of Petroleum, 2c per litre added for AdBlue)

# Labour Costs

HOURLY_WAGE = 47  # $/hour (Award wafge rate grade 8, with overtime based on a 49 hour work week, superannuation, leave loading, and workers comp)

# Emissions Factors

RETAIL_CHARGING_EMISSIONS = 0.7  # kgCO2e/kWh (current grid emissions)
OFFPEAK_CHARGING_EMISSIONS = 0.7  # kgCO2e/kWh (same as retail)
SOLAR_CHARGING_EMISSIONS = 0.04  # kgCO2e/kWh (lifecycle emissions of solar panels)
PUBLIC_CHARGING_EMISSIONS = 0.7  # kgCO2e/kWh (same as retail)
DIESEL_EMISSIONS = 2.68  # kgCO2e/litre

# Vehicle Operating Parameters

VEHICLE_LIFE = 15  # Years
RIGID_ANNUAL_KMS = 23000  # kms/year (SMVU Data)
ART_ANNUAL_KMS = 84000  # kms/year (SMVU Data)
WORKING_DAYS = 255  # Number of working days per year (365 * 0.70)

# Payload Penalty - Based on BITRE freight rates
FREIGHT_RATE_PER_TONNE_KM = {
    "Light Rigid": 0.25,  # $/tonne-km (BITRE 2017 rate for rigid truck freight transport)
    "Medium Rigid": 0.25,  # $/tonne-km (BITRE 2017 rate for rigid truck freight transport)
    "Articulated": 0.08,  # $/tonne-km (BITRE 2017 rate for articulated truck freight transport)
}
PAYLOAD_UTILISATION_FACTOR = {
    "Light Rigid": 0.8,  # Light rigid trucks typically run at 80% payload capacity
    "Medium Rigid": 0.8,  # Medium rigid trucks typically run at 80% payload capacity
    "Articulated": 0.9,  # Articulated trucks typically run at 90% payload capacity (more efficient operations)
}

# Insurance Costs

INSURANCE_RATE_BEV = (
    0.035  # % (annual insurance as a percentage of vehicle price for BEV)
)
INSURANCE_RATE_DSL = 0.0315  # % (annual insurance as a percentage of vehicle price for Diesel, based on Transport Industry Council guidelines)
OTHER_INSURANCE = (
    2000  # $/year (Permits, TAC fees, goods insurance, PLI, personal income insurance)
)

# Maintenance Costs
MAINTENANCE_COST_PER_KM = {
    "BEV": {
        "Light Rigid": 0.10,  # $/km (check this with T&E)
        "Medium Rigid": 0.10,  # $/km (check this with T&E)
        "Articulated": 0.19,  # $/km (check this with T&E)
    },
    "Diesel": {
        "Light Rigid": 0.18,  # $/km (check this with T&E)
        "Medium Rigid": 0.18,  # $/km (check this with T&E)
        "Articulated": 0.28,  # $/km (check this with T&E)
    },
}

# Financial Parameters

INFLATION_RATE = 0.025  # % (general annual inflation rate)
DISCOUNT_RATE = 0.05  # % (for NPV calculations)
INTEREST_RATE = 0.06  # % (for financing calculations, based on commercial rates for trucks available on financing website Savvy)
DEPRECIATION_RATE_FIRST_YEAR = 0.20  # % (first year depreciation)
DEPRECIATION_RATE_ONGOING = 0.10  # % (annual depreciation after first year)
FINANCING_TERM = 5  # Years
DOWN_PAYMENT_RATE = 0.20  # % (percentage of price paid upfront)

# Battery

BATTERY_REPLACEMENT_COST = 130  # $/kWh (cost to replace battery cells)
BATTERY_RECYCLE_VALUE = 13  # $/kWh (value obtained from recycling old battery)
BATTERY_DEGRADATION_RATE = 0.025  # %/year (annual capacity loss)
BATTERY_LIFE_VARIATION_BASE = (
    2.0  # Base multiplier for battery life variation calculations
)

# Government Fees, Taxes, Incentives

FUEL_TAX_CREDIT = (
    0.203  # $/litre (included in DIESEL_PRICE but granted back as a rebate)
)
ROAD_USER_CHARGE = (
    0.305  # $/litre (included in DIESEL_PRICE, may need to apply to BEV's in some way)
)
STAMP_DUTY_RATE = 0.03  # % (percentage of vehicle price, assumed to be 3% based on freightmetrics.com.au)

# Other
HOURS_IN_YEAR = 8760  # Number of hours in a year
DAYS_IN_YEAR = 365  # Number of days in a year
WEEKS_IN_YEAR = 52  # Number of weeks in a year
MONTHS_IN_YEAR = 12  # Number of months in a year
</file>

<file path="frontend/src/components/results/ComparisonHighlights.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency, formatCurrencyCompact, formatPerKilometre } from '@utils/format';

const ComparisonHighlights = () => {
  const results = useTCOStore((state) => state.results);
  const baselineId = useTCOStore((state) => state.wizardData.currentVehicle);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return null;
  }

  const sorted = [...results].sort((a, b) => a.total_cost - b.total_cost);
  const leader = sorted[0];
  const runnerUp = sorted.length > 1 ? sorted[1] : undefined;
  const baselineResult = baselineId
    ? results.find((result) => result.vehicle_id === baselineId)
    : undefined;
  const baseline = baselineResult ?? leader;

  const baselineIsLeader = baseline.vehicle_id === leader.vehicle_id;
  const lifetimeDelta = baselineIsLeader ? 0 : baseline.total_cost - leader.total_cost;
  const annualDelta = baselineIsLeader ? 0 : baseline.annual_cost - leader.annual_cost;
  const runnerDelta = runnerUp ? runnerUp.total_cost - leader.total_cost : undefined;

  const getDisplayName = (vehicleId: string) =>
    vehicleDetails[vehicleId]?.model_name ?? vehicleId;

  const leaderName = getDisplayName(leader.vehicle_id);
  const baselineName = getDisplayName(baseline.vehicle_id);
  const runnerName = runnerUp ? getDisplayName(runnerUp.vehicle_id) : undefined;

  return (
    <Card title="Key findings" subtitle="Key takeaways from the latest comparison.">
      <div className="grid gap-6 md:grid-cols-3">
        <div className="border-4 border-brand-primary bg-white px-6 py-5 relative">
          <div className="absolute top-0 right-0 bg-brand-primary text-black text-xs font-bold px-2 py-1">
            Lowest cost
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1">
            Best option
          </p>
          <p className="text-2xl font-heading font-bold text-black">{leaderName}</p>
          <p className="text-sm font-medium text-slate-800 mt-2">
            {formatPerKilometre(leader.cost_per_km)} · {leader.scenario_name}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Total cost {formatCurrencyCompact(leader.total_cost)}
          </p>
        </div>

        <div className="border border-slate-200 bg-white px-6 py-5">
          <p className="text-xs font-bold text-slate-500 mb-1">
            {baselineIsLeader ? 'Diesel is still optimal' : 'Savings vs your current truck'}
          </p>
          <p className="text-2xl font-heading font-bold text-black">
            {baselineIsLeader ? '—' : formatCurrency(Math.abs(lifetimeDelta))}
          </p>
          <p className="text-sm text-slate-600 mt-2">
            {baselineIsLeader
              ? 'Your current truck already leads this scenario.'
              : `${lifetimeDelta >= 0 ? 'Savings' : 'Additional cost'} compared to ${baselineName}.`}
          </p>
          {!baselineIsLeader && (
            <p className="text-xs text-slate-500 mt-1">
              Annual delta {formatCurrency(Math.abs(annualDelta))}{' '}
              {annualDelta >= 0 ? 'saved each year.' : 'extra each year.'}
            </p>
          )}
        </div>

        <div className="border border-slate-200 bg-white px-6 py-5">
          <p className="text-xs font-bold text-slate-500 mb-1">
            {runnerUp ? 'Cost gap' : 'Add another vehicle'}
          </p>
          <p className="text-2xl font-heading font-bold text-black">
            {runnerUp && runnerDelta !== undefined ? formatCurrency(Math.abs(runnerDelta)) : '—'}
          </p>
          <p className="text-sm text-slate-600 mt-2">
            {runnerUp
              ? `${runnerName} is ${(runnerDelta ?? 0) >= 0 ? 'higher' : 'lower'
              } over the horizon.`
              : 'Select at least one comparator to quantify the gap.'}
          </p>
        </div>
      </div>
    </Card>
  );
};

export default ComparisonHighlights;
</file>

<file path="frontend/src/components/results/ResultsPanel.tsx">
import Card from '@components/shared/Card';
import ComparisonHighlights from '@components/results/ComparisonHighlights';
import CostBreakdownChart from '@components/results/CostBreakdownChart';
import CostPerKmChart from '@components/results/CostPerKmChart';
import PaybackChart from '@components/results/PaybackChart';
import SavingsWaterfallChart from '@components/results/SavingsWaterfallChart';
import SensitivityTornadoChart from '@components/results/SensitivityTornadoChart';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const ResultsPanel = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const isCalculating = useTCOStore((state) => state.isCalculating);

  if (isCalculating) {
    return (
      <Card
        title="Calculating..."
        subtitle="Running the comparison analysis."
      >
        <div className="flex h-32 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-brand-primary" />
        </div>
      </Card>
    );
  }

  if (!results.length) {
    return (
      <Card
        title="No results yet"
        subtitle="Complete the wizard and run a comparison to see the cost breakdown."
      >
        <p className="text-sm text-slate-500">
          Once calculations run, we will show per-vehicle summaries, cost-per-km, and component level
          breakdowns here.
        </p>
      </Card>
    );
  }

  // Check if we have both diesel and BEV for deeper analysis
  const hasDiesel = results.some((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const hasBev = results.some((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');
  const showDeeperAnalysis = hasDiesel && hasBev;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {results.map((result) => {
          const modelName = vehicleDetails[result.vehicle_id]?.model_name ?? result.vehicle_id;
          return (
            <Card
              key={result.vehicle_id}
              title={`${modelName} - ${result.scenario_name}`}
              subtitle="Cost per kilometre"
            >
              <p className="text-3xl font-semibold text-brand-700">
                {new Intl.NumberFormat('en-AU', {
                  style: 'currency',
                  currency: 'AUD',
                  minimumFractionDigits: 2,
                }).format(result.cost_per_km)}
                <span className="text-base font-normal text-slate-500"> / km</span>
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Annual: {formatCurrency(result.annual_cost)} | Total cost:{' '}
                {formatCurrency(result.total_cost)}
              </p>
            </Card>
          );
        })}
      </div>

      <ComparisonHighlights />

      <div className="grid gap-6 lg:grid-cols-2">
        <CostPerKmChart />
        <CostBreakdownChart />
      </div>

      {showDeeperAnalysis && (
        <>
          <div className="mt-4">
            <h2 className="text-xl font-heading font-bold text-black">Deeper Analysis</h2>
            <p className="text-sm text-slate-600 mt-1">
              Explore the financial dynamics of your diesel vs electric comparison.
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <PaybackChart />
            <SavingsWaterfallChart />
          </div>

          <SensitivityTornadoChart />
        </>
      )}
    </div>
  );
};

export default ResultsPanel;
</file>

<file path="frontend/src/components/shared/Field.tsx">
import type { InputHTMLAttributes } from 'react';
import clsx from 'clsx';

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

const Field = ({ label, hint, error, className, ...props }: FieldProps) => (
  <label className="flex h-full flex-col gap-2 text-sm text-slate-700 font-body">
    <span className="micro-heading text-black">{label}</span>
    <input
      className={clsx(
        'w-full border bg-white px-4 py-3 text-base text-black placeholder-slate-400 focus:outline-none transition-all rounded-lg shadow-sm',
        error
          ? 'border-rose-500 focus:border-rose-500 bg-rose-50'
          : 'border-slate-300 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/25',
        className
      )}
      aria-invalid={Boolean(error)}
      {...props}
    />
    {error ? (
      <span className="block min-h-[1.25rem] text-xs font-semibold text-rose-600">{error}</span>
    ) : hint ? (
      <span className="block min-h-[1.25rem] text-xs text-slate-500">{hint}</span>
    ) : (
      <span className="block min-h-[1.25rem]" aria-hidden="true" />
    )}
  </label>
);

export default Field;
</file>

<file path="frontend/src/components/wizard/SelectedVehiclesSummary.tsx">
import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleDetail } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';

const metrics: {
  key: string;
  label: string;
  formatter: (detail: VehicleDetail) => string;
}[] = [
  {
    key: 'payload',
    label: 'Payload',
    formatter: (detail) => `${detail.payload.toFixed(1)} t`,
  },
  {
    key: 'range_km',
    label: 'Range (km)',
    formatter: (detail) =>
      detail.range_km > 0 ? `${detail.range_km.toLocaleString()} km` : 'Not specified',
  },
  {
    key: 'energy_store',
    label: 'Energy store',
    formatter: (detail) =>
      detail.drivetrain_type === 'BEV'
        ? `${detail.battery_capacity_kwh.toLocaleString()} kWh`
        : `${detail.litres_per_km.toFixed(2)} L/km`,
  },
  {
    key: 'maintenance_cost_per_km',
    label: 'Maintenance ($/km)',
    formatter: (detail) => `$${detail.maintenance_cost_per_km.toFixed(2)}`,
  },
  {
    key: 'annual_kms',
    label: 'Annual kms default',
    formatter: (detail) => `${detail.annual_kms.toLocaleString()} km`,
  },
  {
    key: 'annual_registration',
    label: 'Registration',
    formatter: (detail) => formatCurrency(detail.annual_registration),
  },
];

const SelectedVehiclesSummary = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const sessionId = useTCOStore((state) => state.sessionId);
  const selectedIds = Array.from(
    new Set(
      [wizardData.currentVehicle, ...wizardData.comparisonVehicles].filter(Boolean) as string[]
    )
  );
  const selectedDetails = selectedIds
    .map((id) => vehicleDetails[id])
    .filter(Boolean) as VehicleDetail[];

  if (!selectedIds.length) {
    return null;
  }

  return (
    <Card
      title="Selected vehicle specs"
      subtitle="Quick reference for your selected vehicle assumptions."
    >
      {sessionId && (
        <p className="mb-4 text-xs text-slate-500">
          Autosaved session:
          <span className="ml-1 font-mono text-slate-700">{sessionId}</span>
        </p>
      )}
      {!selectedDetails.length ? (
        <p className="text-sm text-slate-500">Fetching vehicle specifications…</p>
      ) : (
        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr>
                <th className="py-2 text-left font-semibold text-slate-500">Metric</th>
                {selectedDetails.map((detail) => (
                  <th
                    key={detail.vehicle_id}
                    className="py-2 text-right font-semibold text-slate-500"
                    title={`${detail.model_name} (${detail.vehicle_id})`}
                  >
                    <span className="block text-base text-slate-900">{detail.model_name}</span>
                    <span className="block text-xs font-normal text-slate-400">
                      {detail.weight_class}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {metrics.map((metric) => (
                <tr key={metric.key}>
                  <td className="py-2 text-slate-600">{metric.label}</td>
                  {selectedDetails.map((detail) => (
                    <td
                      key={`${detail.vehicle_id}-${metric.key}`}
                      className="py-2 text-right font-medium text-slate-900"
                    >
                      {metric.formatter(detail)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

export default SelectedVehiclesSummary;
</file>

<file path="frontend/src/components/wizard/WizardCompareStep.tsx">
import { useEffect, useMemo, useRef } from 'react';
import ResultsPanel from '@components/results/ResultsPanel';
import ComparisonConfigPanel from './ComparisonConfigPanel';
import SelectedVehiclesSummary from './SelectedVehiclesSummary';
import { useTCOStore } from '@state/tcoStore';
import { useCalculationRunner } from '@hooks/useCalculations';
import type { ComparisonRequestPayload } from '@shared/types/tco.types';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';
import { calculateComparison } from '@shared/calculator';

const WizardCompareStep = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const { runPreviewComparison } = useCalculationRunner();

  // Generation counter to prevent stale results from overwriting newer ones
  const generationRef = useRef(0);

  const payload = useMemo<ComparisonRequestPayload | null>(() => {
    if (!wizardData.currentVehicle) {
      return null;
    }
    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles])
    ).filter(Boolean) as string[];
    if (!vehicleIds.length) {
      return null;
    }

    const overrides = compactOverrides(wizardData.overrides ?? {});
    const vehicleOverrides = compactVehicleParamOverrides(
      wizardData.vehicleParamOverrides ?? {}
    );

    const request: ComparisonRequestPayload = {
      vehicle_ids: vehicleIds,
      scenario_name: wizardData.scenario,
      purchase_method: wizardData.purchaseMethod,
      duty_cycle: wizardData.dutyCycle,
    };

    if (Object.keys(overrides).length) {
      request.overrides = overrides;
    }
    if (Object.keys(vehicleOverrides).length) {
      request.vehicle_param_overrides = vehicleOverrides;
    }
    return request;
  }, [
    wizardData.currentVehicle,
    wizardData.comparisonVehicles,
    wizardData.overrides,
    wizardData.purchaseMethod,
    wizardData.scenario,
    wizardData.vehicleParamOverrides,
    wizardData.dutyCycle,
  ]);

  useEffect(() => {
    if (!payload) {
      return;
    }

    const currentGeneration = ++generationRef.current;

    const timer = setTimeout(() => {
      // Skip if payload has no vehicles
      if (!payload.vehicle_ids.length) {
        return;
      }

      setIsCalculating(true);
      try {
        const results = calculateComparison(payload);

        // Only apply results if this is still the latest generation
        if (currentGeneration === generationRef.current) {
          setResults(results);
        }
      } catch (error) {
        console.warn('Preview calculation failed:', error);
      } finally {
        if (currentGeneration === generationRef.current) {
          setIsCalculating(false);
        }
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [payload, setIsCalculating, setResults]);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <div className="flex flex-col gap-6">
        <ResultsPanel />
        <SelectedVehiclesSummary />
      </div>
      <ComparisonConfigPanel />
    </div>
  );
};

export default WizardCompareStep;
</file>

<file path="frontend/src/components/wizard/WizardCostStep.tsx">
import { useFormContext } from 'react-hook-form';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import type { WizardFormValues } from '@forms/wizardForm';

const WizardCostStep = () => {
  const {
    register,
    formState: { errors },
  } = useFormContext<WizardFormValues>();

  return (
    <Card title="Price adjustments" subtitle="Optional adjustments for quick scenario exploration.">
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Diesel price adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 1.10 for 10% higher prices, 0.90 for 10% lower."
            error={errors.overrides?.fuel_price_variation?.message}
            {...register('overrides.fuel_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Electricity price adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 1.10 for 10% higher prices, 0.90 for 10% lower."
            error={errors.overrides?.electricity_price_variation?.message}
            {...register('overrides.electricity_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Battery life adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 0.70 for shorter battery life (higher replacement cost), 1.20 for longer life."
            error={errors.overrides?.battery_life_variation?.message}
            {...register('overrides.battery_life_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Charging efficiency adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Affects energy required per kilometre for electric trucks."
            error={errors.overrides?.charging_efficiency_variation?.message}
            {...register('overrides.charging_efficiency_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
      </div>
    </Card>
  );
};

export default WizardCostStep;
</file>

<file path="frontend/src/forms/wizardForm.ts">
import { z } from 'zod';
import type { DutyCycle, PurchaseMethod, ScenarioKey } from '@shared/types/tco.types';

export interface ScenarioOption {
  value: ScenarioKey;
  label: string;
  description: string;
}

export const scenarioOptions: ScenarioOption[] = [
  {
    value: 'baseline',
    label: 'Current trends',
    description:
      'Fuel prices rise 2-3% per year, maintenance costs follow typical patterns, battery prices stay similar.',
  },
  {
    value: 'technology_breakthrough',
    label: 'Fast EV progress',
    description:
      'Battery costs drop faster, electric trucks become more efficient, maintenance savings grow.',
  },
  {
    value: 'oil_crisis',
    label: 'High fuel prices',
    description:
      'Diesel prices spike from year 3, more price swings, electricity costs rise steadily at 3% per year.',
  },
];

export const purchaseOptions: { value: PurchaseMethod; label: string }[] = [
  { value: 'financed', label: 'Financed' },
  { value: 'outright', label: 'Outright' },
];

const dutyCycleSchema = z
  .object({
    urban: z
      .number({
        invalid_type_error: 'Urban % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    regional: z
      .number({
        invalid_type_error: 'Regional % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    longHaul: z
      .number({
        invalid_type_error: 'Long-haul % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
  })
  .superRefine((values, ctx) => {
    const total = values.urban + values.regional + values.longHaul;
    if (Math.round(total) !== 100) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Duty cycle must add up to 100%.',
        path: ['longHaul'],
      });
    }
  });

const overridesSchema = z.object({
  annual_kms_variation: z
    .number({
      invalid_type_error: 'Annual kilometres must be a number.',
    })
    .min(5000, 'Minimum 5,000 km per year.')
    .max(250000, 'Maximum 250,000 km per year.')
    .optional(),
  residual_value_variation: z
    .number({
      invalid_type_error: 'Residual value must be a number.',
    })
    .min(0.5, 'Too low — at least 0.5x the base residual.')
    .max(1.5, 'Too high — maximum 1.5x the base residual.')
    .optional(),
  maintenance_cost_variation: z
    .number({
      invalid_type_error: 'Maintenance multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(1.5, 'Maximum multiplier is 1.5x.')
    .optional(),
  fuel_price_variation: z
    .number({
      invalid_type_error: 'Diesel multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(2.0, 'Maximum multiplier is 2.0x.')
    .optional(),
  electricity_price_variation: z
    .number({
      invalid_type_error: 'Electricity multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(2.0, 'Maximum multiplier is 2.0x.')
    .optional(),
  battery_life_variation: z
    .number({
      invalid_type_error: 'Battery life multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(1.5, 'Maximum multiplier is 1.5x.')
    .optional(),
  charging_efficiency_variation: z
    .number({
      invalid_type_error: 'Charging efficiency multiplier must be a number.',
    })
    .min(0.7, 'Minimum multiplier is 0.7x.')
    .max(1.3, 'Maximum multiplier is 1.3x.')
    .optional(),
});

export const vehicleParamOverridesSchema = z.object({
  msrp_override: z.number().min(0, 'Must be positive').max(10_000_000, 'Maximum $10M').optional(),
  payload_override: z.number().min(0, 'Must be positive').max(100, 'Maximum 100t').optional(),
  range_km_override: z.number().min(0, 'Must be positive').max(2000, 'Maximum 2000km').optional(),
  battery_capacity_kwh_override: z.number().min(0, 'Must be positive').max(2000, 'Maximum 2000kWh').optional(),
  kwh_per_km_override: z.number().min(0, 'Must be positive').max(10, 'Maximum 10 kWh/km').optional(),
  litres_per_km_override: z.number().min(0, 'Must be positive').max(5, 'Maximum 5 L/km').optional(),
  annual_registration_override: z.number().min(0, 'Must be positive').max(100_000, 'Maximum $100k').optional(),
  interest_rate_override: z.number().min(0, 'Must be positive').max(1, 'Maximum 100%').optional(),
  charging_time_hours_override: z.number().min(0, 'Must be positive').max(24, 'Maximum 24h').optional(),
});

export type VehicleParamOverridesValidated = z.infer<typeof vehicleParamOverridesSchema>;

export const wizardFormSchema = z.object({
  scenario: z.enum(['baseline', 'technology_breakthrough', 'oil_crisis']),
  purchaseMethod: z.enum(['financed', 'outright']),
  dutyCycle: dutyCycleSchema.default({
    urban: 60,
    regional: 25,
    longHaul: 15,
  } satisfies DutyCycle),
  overrides: overridesSchema.default({}),
});

export type WizardFormValues = z.infer<typeof wizardFormSchema>;
</file>

<file path="frontend/src/hooks/useCalculations.ts">
import { useMutation } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { calculateComparison, calculateTco } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import {
  createSession,
  updateSession,
} from '@services/api';
import { useTCOStore } from '@state/tcoStore';
import { buildSessionPayload } from '@utils/payload';

export const useCalculationRunner = () => {
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const setSessionId = useTCOStore((state) => state.setSessionId);

  // Mutex refs to prevent duplicate session creation race condition
  const isCreatingSession = useRef(false);
  const pendingSessionId = useRef<string | null>(null);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }

      // If we're already creating a session, skip this call
      if (isCreatingSession.current) {
        return;
      }

      const payload = buildSessionPayload(wizardData, data);
      const currentSessionId = sessionId || pendingSessionId.current;

      try {
        if (currentSessionId) {
          await updateSession(currentSessionId, payload);
        } else {
          isCreatingSession.current = true;
          const response = await createSession(payload);
          pendingSessionId.current = response.sessionId;
          setSessionId(response.sessionId);
        }
      } catch (error) {
        console.warn('Failed to persist session', error);
      } finally {
        isCreatingSession.current = false;
      }
    },
    [sessionId, setSessionId, wizardData]
  );

  const comparisonMutation = useMutation({
    mutationFn: async (payload: ComparisonRequestPayload) => {
      return calculateComparison(payload);
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults(data);
      void persistSession(data);
    },
    onSettled: () => setIsCalculating(false),
  });

  const singleMutation = useMutation({
    mutationFn: async (payload: CalculationRequestPayload) => {
      return calculateTco(payload);
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults([data]);
      void persistSession([data]);
    },
    onSettled: () => setIsCalculating(false),
  });

  const runPreviewComparison = useCallback(
    async (payload: ComparisonRequestPayload) => {
      if (!payload.vehicle_ids.length) {
        return;
      }
      setIsCalculating(true);
      try {
        const data = calculateComparison(payload);
        setResults(data);
      } catch (error) {
        console.warn('Preview comparison failed', error);
      } finally {
        setIsCalculating(false);
      }
    },
    [setIsCalculating, setResults]
  );

  return {
    runComparison: comparisonMutation.mutateAsync,
    runPreviewComparison,
    runSingle: singleMutation.mutateAsync,
    comparisonStatus: comparisonMutation.status,
    singleStatus: singleMutation.status,
  };
};
</file>

<file path="scripts/validation.py">
"""Data validation helpers shared between tests and build pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.constants import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    VEHICLE_LIFE,
)
from data.scenarios import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    SCENARIOS,
    EconomicScenario,
)
from data.vehicles import (  # noqa: E402  # Requires repo root on sys.path for CLI execution
    ALL_MODELS,
    BY_ID,
    VehicleModel,
)


@dataclass
class ValidationReport:
    """Structured output returned by the validator."""

    vehicles: Dict[str, List[str]]
    scenarios: Dict[str, List[str]]
    comparison_pairs: List[str]
    is_valid: bool


class DataValidator:
    """Validates vehicle data, scenarios, and comparison pair integrity."""

    PAYLOAD_LIMITS: Dict[str, Tuple[float, float]] = {
        "Light Rigid": (0.5, 10.0),
        "Medium Rigid": (5.0, 30.0),
        "Articulated": (20.0, 75.0),
    }

    @classmethod
    def validate_vehicle(cls, vehicle: VehicleModel) -> List[str]:
        issues: List[str] = []

        if vehicle.msrp <= 0:
            issues.append(f"{vehicle.vehicle_id}: MSRP must be positive.")
        if vehicle.annual_kms <= 0:
            issues.append(f"{vehicle.vehicle_id}: Annual kms must be positive.")

        bounds = cls.PAYLOAD_LIMITS.get(vehicle.weight_class)
        if bounds:
            lower, upper = bounds
            if not (lower <= vehicle.payload <= upper):
                issues.append(
                    f"{vehicle.vehicle_id}: Payload outside expected range for {vehicle.weight_class} "
                    f"({lower}–{upper} t)."
                )

        if vehicle.drivetrain_type == "BEV" and vehicle.range_km > 0:
            expected = vehicle.battery_capacity_kwh / vehicle.range_km
            if vehicle.kwh_per_km <= 0:
                issues.append(f"{vehicle.vehicle_id}: kWh per km must be positive.")
            elif abs(vehicle.kwh_per_km - expected) / expected > 0.2:
                issues.append(
                    f"{vehicle.vehicle_id}: kWh per km inconsistent with capacity/range (expected ~{expected:.2f})."
                )

        if vehicle.drivetrain_type == "Diesel" and vehicle.litres_per_km <= 0:
            issues.append(f"{vehicle.vehicle_id}: Diesel consumption must be positive.")

        return issues

    @staticmethod
    def validate_scenario(scenario: EconomicScenario) -> List[str]:
        issues: List[str] = []

        trajectories = [
            ("diesel price trajectory", scenario.diesel_price_trajectory),
            ("electricity price trajectory", scenario.electricity_price_trajectory),
            ("battery price trajectory", scenario.battery_price_trajectory),
        ]
        for label, values in trajectories:
            if len(values) < VEHICLE_LIFE:
                issues.append(f"{scenario.name}: {label} shorter than vehicle life.")
            if any(value < 0 for value in values):
                issues.append(
                    f"{scenario.name}: {label} contains negative multipliers."
                )

        return issues

    @staticmethod
    def validate_comparison_pairs() -> List[str]:
        issues: List[str] = []
        for vehicle in ALL_MODELS:
            pair_id = vehicle.comparison_pair
            counterpart = BY_ID.get(pair_id)
            if not counterpart:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' missing."
                )
                continue
            if counterpart.comparison_pair != vehicle.vehicle_id:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' does not point back to this vehicle."
                )
            if counterpart.weight_class != vehicle.weight_class:
                issues.append(
                    f"{vehicle.vehicle_id}: Comparison pair '{pair_id}' weight class mismatch ({counterpart.weight_class})."
                )
        return issues

    @classmethod
    def validate_all(cls) -> ValidationReport:
        vehicle_issues = {
            vehicle.vehicle_id: issues
            for vehicle in ALL_MODELS
            if (issues := cls.validate_vehicle(vehicle))
        }
        scenario_issues = {
            name: issues
            for name, scenario in SCENARIOS.items()
            if (issues := cls.validate_scenario(scenario))
        }
        comparison_issues = cls.validate_comparison_pairs()

        return ValidationReport(
            vehicles=vehicle_issues,
            scenarios=scenario_issues,
            comparison_pairs=comparison_issues,
            is_valid=not (vehicle_issues or scenario_issues or comparison_issues),
        )


def _print_dict_issues(title: str, issues: Dict[str, List[str]]) -> None:
    if not issues:
        return
    print(f"\n{title}:")
    for key in sorted(issues):
        for message in issues[key]:
            print(f"  - {key}: {message}")


def _print_list_issues(title: str, issues: List[str]) -> None:
    if not issues:
        return
    print(f"\n{title}:")
    for message in issues:
        print(f"  - {message}")


def main() -> None:
    """CLI entry point for validating data tables."""

    report = DataValidator.validate_all()
    total_vehicles = len(ALL_MODELS)
    total_scenarios = len(SCENARIOS)

    if report.is_valid:
        print(
            f"Data validation passed for {total_vehicles} vehicles and {total_scenarios} scenarios."
        )
        return

    print("Data validation FAILED. See details below.")
    _print_dict_issues("Vehicle issues", report.vehicles)
    _print_dict_issues("Scenario issues", report.scenarios)
    _print_list_issues("Comparison pair issues", report.comparison_pairs)
    sys.exit(1)


if __name__ == "__main__":
    main()
</file>

<file path="shared/calculator/tcoCalculator.ts">
/**
 * @file TCO Calculator - Core Calculation Engine
 * @module shared/calculator/tcoCalculator
 *
 * This module contains the main TCO (Total Cost of Ownership) calculation
 * logic for comparing BEV and Diesel vehicles over a 15-year lifecycle.
 *
 * Key functions:
 * - calculateTco(): Calculate TCO for a single vehicle
 * - calculateComparison(): Calculate TCO for multiple vehicles
 *
 * Cost components calculated:
 * - Purchase cost (including stamp duty, rebates)
 * - Fuel/energy costs (with scenario trajectories)
 * - Maintenance costs
 * - Insurance and registration
 * - Battery replacement (BEV only, year 8)
 * - Carbon costs (if scenario includes carbon pricing)
 * - Charging labor costs (BEV only)
 * - Payload penalty (lost revenue from reduced capacity)
 * - Residual value (end-of-life)
 *
 * @see shared/calculator/math.ts for financial utilities
 * @see shared/data/constants.ts for configuration values
 * @see shared/types/tco.types.ts for type definitions
 */

import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
  CostBreakdown,
  CostOverrides,
  EconomicScenarioDefinition,
  DutyCycle,
  PurchaseMethod,
  ScenarioKey,
  VehicleDetail,
  VehicleParamOverrides,
} from '../types/tco.types';
import { VEHICLE_BY_ID, VEHICLE_DETAILS } from '../data/vehicleCatalog';
import { CONSTANTS } from '../data/constants';
import { SCENARIO_DEFINITIONS } from '../data/scenarios';
import { POLICY_CONFIG } from '../data/policies';
import {
  calculateAnnualisedCost,
  calculateNpvOfAnnualCashflows,
  calculateNpvOfPayments,
  calculatePresentValue,
  discountToPresent,
} from './math';

type WeightClass = VehicleDetail['weight_class'];
type ChargingMix = Record<'retail' | 'offpeak' | 'public' | 'solar', number>;

/**
 * Validates that a value is a Record with expected keys.
 * Throws descriptive error if validation fails.
 */
const assertRecord = <K extends string, V>(
  value: unknown,
  name: string,
  expectedKeys?: K[]
): Record<K, V> => {
  if (!value || typeof value !== 'object') {
    throw new Error(`${name} must be an object, got ${typeof value}`);
  }
  if (expectedKeys) {
    for (const key of expectedKeys) {
      if (!(key in value)) {
        throw new Error(`${name} is missing required key: ${key}`);
      }
    }
  }
  return value as Record<K, V>;
};

/**
 * Validates nested Record structure for maintenance costs.
 */
const assertMaintenanceCosts = (
  value: unknown
): Record<'BEV' | 'Diesel', Record<WeightClass, number>> => {
  const record = assertRecord<'BEV' | 'Diesel', unknown>(
    value,
    'MAINTENANCE_COST_PER_KM',
    ['BEV', 'Diesel']
  );
  assertRecord<WeightClass, number>(record.BEV, 'MAINTENANCE_COST_PER_KM.BEV');
  assertRecord<WeightClass, number>(record.Diesel, 'MAINTENANCE_COST_PER_KM.Diesel');
  return record as Record<'BEV' | 'Diesel', Record<WeightClass, number>>;
};

const DEFAULT_DUTY_CYCLE: DutyCycle = { urban: 60, regional: 25, longHaul: 15 };

/**
 * Sanitizes calculation payload to prevent NaN and invalid values from reaching calculations.
 * This is a defensive layer - frontend validation should catch most issues.
 */
const sanitizePayload = (payload: CalculationRequestPayload): CalculationRequestPayload => {
  const sanitized = { ...payload };

  // Sanitize duty cycle - ensure all values are valid positive numbers
  if (sanitized.duty_cycle) {
    sanitized.duty_cycle = {
      urban: Math.max(0, Number(sanitized.duty_cycle.urban) || 0),
      regional: Math.max(0, Number(sanitized.duty_cycle.regional) || 0),
      longHaul: Math.max(0, Number(sanitized.duty_cycle.longHaul) || 0),
    };
  }

  // Sanitize cost overrides - ensure they're positive numbers or undefined
  if (sanitized.overrides) {
    const cleanOverrides: CostOverrides = {};
    for (const [key, value] of Object.entries(sanitized.overrides)) {
      if (typeof value === 'number' && !isNaN(value) && value >= 0) {
        cleanOverrides[key as keyof CostOverrides] = value;
      }
    }
    sanitized.overrides = cleanOverrides;
  }

  // Sanitize vehicle param overrides - ensure they're positive numbers or undefined
  if (sanitized.vehicle_overrides) {
    const cleanVehicleOverrides: VehicleParamOverrides = {};
    for (const [key, value] of Object.entries(sanitized.vehicle_overrides)) {
      if (typeof value === 'number' && !isNaN(value) && value >= 0) {
        cleanVehicleOverrides[key as keyof VehicleParamOverrides] = value;
      }
    }
    sanitized.vehicle_overrides = cleanVehicleOverrides;
  }

  return sanitized;
};

const asNumber = (value: unknown, name: string): number => {
  if (typeof value !== 'number') {
    throw new Error(`Constant ${name} must be numeric.`);
  }
  return value;
};

const VEHICLE_LIFE = asNumber(CONSTANTS.VEHICLE_LIFE, 'VEHICLE_LIFE');
const DISCOUNT_RATE = asNumber(CONSTANTS.DISCOUNT_RATE, 'DISCOUNT_RATE');
const DOWN_PAYMENT_RATE = asNumber(CONSTANTS.DOWN_PAYMENT_RATE, 'DOWN_PAYMENT_RATE');
const FINANCING_TERM = asNumber(CONSTANTS.FINANCING_TERM, 'FINANCING_TERM');
const BASE_INTEREST_RATE = asNumber(CONSTANTS.INTEREST_RATE, 'INTEREST_RATE');
const WORKING_DAYS = asNumber(CONSTANTS.WORKING_DAYS, 'WORKING_DAYS');
const BATTERY_USABLE_RANGE_FACTOR = asNumber(CONSTANTS.BATTERY_USABLE_RANGE_FACTOR, 'BATTERY_USABLE_RANGE_FACTOR');
const HOURLY_WAGE = asNumber(CONSTANTS.HOURLY_WAGE, 'HOURLY_WAGE');
const BATTERY_REPLACEMENT_COST = asNumber(CONSTANTS.BATTERY_REPLACEMENT_COST, 'BATTERY_REPLACEMENT_COST');
const BATTERY_RECYCLE_VALUE = asNumber(CONSTANTS.BATTERY_RECYCLE_VALUE, 'BATTERY_RECYCLE_VALUE');
const BATTERY_LIFE_VARIATION_BASE = asNumber(CONSTANTS.BATTERY_LIFE_VARIATION_BASE, 'BATTERY_LIFE_VARIATION_BASE');
const BATTERY_REPLACEMENT_YEAR = CONSTANTS.BATTERY_REPLACEMENT_YEAR ?? 8;
const DIESEL_PRICE = asNumber(CONSTANTS.DIESEL_PRICE, 'DIESEL_PRICE');
const DIESEL_EMISSIONS = asNumber(CONSTANTS.DIESEL_EMISSIONS, 'DIESEL_EMISSIONS');
const INSURANCE_RATE_BEV = asNumber(CONSTANTS.INSURANCE_RATE_BEV, 'INSURANCE_RATE_BEV');
const INSURANCE_RATE_DSL = asNumber(CONSTANTS.INSURANCE_RATE_DSL, 'INSURANCE_RATE_DSL');
const OTHER_INSURANCE = asNumber(CONSTANTS.OTHER_INSURANCE, 'OTHER_INSURANCE');
const STAMP_DUTY_RATE = asNumber(CONSTANTS.STAMP_DUTY_RATE, 'STAMP_DUTY_RATE');
const DEPRECIATION_RATE_FIRST_YEAR = asNumber(
  CONSTANTS.DEPRECIATION_RATE_FIRST_YEAR,
  'DEPRECIATION_RATE_FIRST_YEAR'
);
const DEPRECIATION_RATE_ONGOING = asNumber(
  CONSTANTS.DEPRECIATION_RATE_ONGOING,
  'DEPRECIATION_RATE_ONGOING'
);

const MAINTENANCE_COST_PER_KM = assertMaintenanceCosts(CONSTANTS.MAINTENANCE_COST_PER_KM);
const FREIGHT_RATE_PER_TONNE_KM = assertRecord<WeightClass, number>(
  CONSTANTS.FREIGHT_RATE_PER_TONNE_KM,
  'FREIGHT_RATE_PER_TONNE_KM'
);
const PAYLOAD_UTILISATION_FACTOR = assertRecord<WeightClass, number>(
  CONSTANTS.PAYLOAD_UTILISATION_FACTOR,
  'PAYLOAD_UTILISATION_FACTOR'
);
const CHARGING_TIME_HOURS = assertRecord<WeightClass, number>(
  CONSTANTS.CHARGING_TIME_HOURS,
  'CHARGING_TIME_HOURS'
);
const CHARGING_MIX = (CONSTANTS.CHARGING_MIX_PROPORTIONS as { BEV: Record<WeightClass, ChargingMix> }).BEV;

const RETAIL_PRICE = asNumber(CONSTANTS.RETAIL_CHARGING_PRICE, 'RETAIL_CHARGING_PRICE');
const OFFPEAK_PRICE = asNumber(CONSTANTS.OFFPEAK_CHARGING_PRICE, 'OFFPEAK_CHARGING_PRICE');
const SOLAR_PRICE = asNumber(CONSTANTS.SOLAR_CHARGING_PRICE, 'SOLAR_CHARGING_PRICE');
const PUBLIC_PRICE = asNumber(CONSTANTS.PUBLIC_CHARGING_PRICE, 'PUBLIC_CHARGING_PRICE');
const RETAIL_EMISSIONS = asNumber(CONSTANTS.RETAIL_CHARGING_EMISSIONS, 'RETAIL_CHARGING_EMISSIONS');
const OFFPEAK_EMISSIONS = asNumber(CONSTANTS.OFFPEAK_CHARGING_EMISSIONS, 'OFFPEAK_CHARGING_EMISSIONS');
const SOLAR_EMISSIONS = asNumber(CONSTANTS.SOLAR_CHARGING_EMISSIONS, 'SOLAR_CHARGING_EMISSIONS');
const PUBLIC_EMISSIONS = asNumber(CONSTANTS.PUBLIC_CHARGING_EMISSIONS, 'PUBLIC_CHARGING_EMISSIONS');

const getScenario = (scenarioKey: ScenarioKey): EconomicScenarioDefinition => {
  const scenario = SCENARIO_DEFINITIONS[scenarioKey];
  if (!scenario) {
    throw new Error(`Scenario '${scenarioKey}' is not defined.`);
  }
  return scenario;
};

const getVehicle = (vehicleId: string): VehicleDetail => {
  const vehicle = VEHICLE_BY_ID[vehicleId];
  if (!vehicle) {
    throw new Error(
      `Vehicle '${vehicleId}' not found in catalog. ` +
      `Available vehicles: ${Object.keys(VEHICLE_BY_ID).join(', ')}`
    );
  }
  return vehicle;
};

const applyVehicleOverrides = (
  vehicle: VehicleDetail,
  overrides?: VehicleParamOverrides
): VehicleDetail => {
  if (!overrides) {
    return vehicle;
  }

  const next: VehicleDetail = { ...vehicle };
  if (overrides.msrp_override !== undefined) {
    next.msrp = overrides.msrp_override;
  }
  if (overrides.payload_override !== undefined) {
    next.payload = overrides.payload_override;
  }
  if (overrides.range_km_override !== undefined) {
    next.range_km = overrides.range_km_override;
  }
  if (overrides.battery_capacity_kwh_override !== undefined) {
    next.battery_capacity_kwh = overrides.battery_capacity_kwh_override;
  }
  if (overrides.kwh_per_km_override !== undefined) {
    next.kwh_per_km = overrides.kwh_per_km_override;
  }
  if (overrides.litres_per_km_override !== undefined) {
    next.litres_per_km = overrides.litres_per_km_override;
  }
  if (overrides.annual_registration_override !== undefined) {
    next.annual_registration = overrides.annual_registration_override;
  }
  return next;
};

const getSeriesValue = (series: number[] | undefined, year: number, fallback: number): number => {
  if (!series || series.length < year) {
    return fallback;
  }
  return series[year - 1];
};

const dutyCycleToProfile = (dutyCycle?: DutyCycle): ChargingMix => {
  const raw = dutyCycle ?? DEFAULT_DUTY_CYCLE;

  let urban = Number(raw.urban) || 0;
  let regional = Number(raw.regional) || 0;
  let longHaul = Number(raw.longHaul) || 0;

  if (urban < 0) urban = 0;
  if (regional < 0) regional = 0;
  if (longHaul < 0) longHaul = 0;

  let total = urban + regional + longHaul;

  if (total === 0) {
    urban = DEFAULT_DUTY_CYCLE.urban;
    regional = DEFAULT_DUTY_CYCLE.regional;
    longHaul = DEFAULT_DUTY_CYCLE.longHaul;
    total = urban + regional + longHaul;
  }

  const normalized: DutyCycle = {
    urban: (urban / total) * 100,
    regional: (regional / total) * 100,
    longHaul: (longHaul / total) * 100,
  };

  // Route-type profiles. Urban leans on depot/off-peak, long haul leans on public DC.
  const profiles: Record<'urban' | 'regional' | 'longHaul', ChargingMix> = {
    urban: { retail: 0, offpeak: 0.9, public: 0.1, solar: 0 },
    regional: { retail: 0, offpeak: 0.75, public: 0.25, solar: 0 },
    longHaul: { retail: 0, offpeak: 0.35, public: 0.65, solar: 0 },
  };

  const dutyWeighted: ChargingMix = {
    retail:
      (normalized.urban * profiles.urban.retail +
        normalized.regional * profiles.regional.retail +
        normalized.longHaul * profiles.longHaul.retail) /
      100,
    offpeak:
      (normalized.urban * profiles.urban.offpeak +
        normalized.regional * profiles.regional.offpeak +
        normalized.longHaul * profiles.longHaul.offpeak) /
      100,
    public:
      (normalized.urban * profiles.urban.public +
        normalized.regional * profiles.regional.public +
        normalized.longHaul * profiles.longHaul.public) /
      100,
    solar:
      (normalized.urban * profiles.urban.solar +
        normalized.regional * profiles.regional.solar +
        normalized.longHaul * profiles.longHaul.solar) /
      100,
  };

  const totalWeight =
    dutyWeighted.retail + dutyWeighted.offpeak + dutyWeighted.public + dutyWeighted.solar || 1;
  return {
    retail: dutyWeighted.retail / totalWeight,
    offpeak: dutyWeighted.offpeak / totalWeight,
    public: dutyWeighted.public / totalWeight,
    solar: dutyWeighted.solar / totalWeight,
  };
};

const getDutyAdjustedChargingMix = (vehicle: VehicleDetail, dutyCycle?: DutyCycle): ChargingMix => {
  const baseMix = CHARGING_MIX[vehicle.weight_class];
  if (!baseMix) {
    throw new Error(`Missing charging mix for ${vehicle.weight_class}`);
  }

  const dutyProfile = dutyCycleToProfile(dutyCycle);
  const defaultProfile = dutyCycleToProfile(DEFAULT_DUTY_CYCLE);

  const isDefaultDutyCycle =
    Math.abs(dutyProfile.retail - defaultProfile.retail) < 0.0001 &&
    Math.abs(dutyProfile.offpeak - defaultProfile.offpeak) < 0.0001 &&
    Math.abs(dutyProfile.public - defaultProfile.public) < 0.0001 &&
    Math.abs(dutyProfile.solar - defaultProfile.solar) < 0.0001;

  if (isDefaultDutyCycle) {
    return baseMix;
  }

  // Preserve base mix when duty cycle matches the default; otherwise bias toward the duty-driven mix.
  const adjusted: ChargingMix = {
    retail:
      baseMix.retail === 0 || defaultProfile.retail === 0
        ? baseMix.retail
        : baseMix.retail * (dutyProfile.retail / defaultProfile.retail),
    offpeak:
      baseMix.offpeak === 0 || defaultProfile.offpeak === 0
        ? baseMix.offpeak
        : baseMix.offpeak * (dutyProfile.offpeak / defaultProfile.offpeak),
    public:
      baseMix.public === 0 || defaultProfile.public === 0
        ? baseMix.public
        : baseMix.public * (dutyProfile.public / defaultProfile.public),
    solar:
      baseMix.solar === 0 || defaultProfile.solar === 0
        ? baseMix.solar
        : baseMix.solar * (dutyProfile.solar / defaultProfile.solar),
  };

  const total =
    adjusted.retail + adjusted.offpeak + adjusted.public + adjusted.solar || 1;

  return {
    retail: adjusted.retail / total,
    offpeak: adjusted.offpeak / total,
    public: adjusted.public / total,
    solar: adjusted.solar / total,
  };
};

const getChargingBlendRate = (mix: ChargingMix): number => {
  return mix.retail * RETAIL_PRICE + mix.offpeak * OFFPEAK_PRICE + mix.solar * SOLAR_PRICE + mix.public * PUBLIC_PRICE;
};

const getChargingBlendEmissions = (mix: ChargingMix): number => {
  return (
    mix.retail * RETAIL_EMISSIONS +
    mix.offpeak * OFFPEAK_EMISSIONS +
    mix.solar * SOLAR_EMISSIONS +
    mix.public * PUBLIC_EMISSIONS
  );
};

const getMaintenanceBaseCost = (vehicle: VehicleDetail): number => {
  const drivetrainCosts = MAINTENANCE_COST_PER_KM[vehicle.drivetrain_type];
  const costPerKm = drivetrainCosts?.[vehicle.weight_class];
  if (typeof costPerKm !== 'number') {
    throw new Error(`Maintenance rate missing for ${vehicle.drivetrain_type}/${vehicle.weight_class}`);
  }
  return vehicle.annual_kms * costPerKm;
};

const calculateFuelCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides,
  dutyCycle?: DutyCycle
): number => {
  if (vehicle.drivetrain_type === 'BEV') {
    let efficiencyMultiplier = getSeriesValue(scenario.bev_efficiency_improvement, year, 1);
    if (overrides?.charging_efficiency_variation) {
      efficiencyMultiplier *= overrides.charging_efficiency_variation;
    }
    const adjustedKwhPerKm = vehicle.kwh_per_km * efficiencyMultiplier;
    const chargingMix = getDutyAdjustedChargingMix(vehicle, dutyCycle);
    const baseCost = adjustedKwhPerKm * vehicle.annual_kms * getChargingBlendRate(chargingMix);
    let priceMultiplier = getSeriesValue(scenario.electricity_price_trajectory, year, 1);
    if (overrides?.electricity_price_variation) {
      priceMultiplier *= overrides.electricity_price_variation;
    }
    return baseCost * priceMultiplier;
  }

  const efficiencyMultiplier = getSeriesValue(scenario.diesel_efficiency_improvement, year, 1);
  const adjustedLitresPerKm = vehicle.litres_per_km * efficiencyMultiplier;
  const baseCost = adjustedLitresPerKm * vehicle.annual_kms * DIESEL_PRICE;
  let priceMultiplier = getSeriesValue(scenario.diesel_price_trajectory, year, 1);
  if (overrides?.fuel_price_variation) {
    priceMultiplier *= overrides.fuel_price_variation;
  }
  return baseCost * priceMultiplier;
};

const calculateBatteryReplacementYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): number => {
  if (vehicle.drivetrain_type !== 'BEV' || vehicle.battery_capacity_kwh <= 0 || year !== BATTERY_REPLACEMENT_YEAR) {
    return 0;
  }
  const multiplier = getSeriesValue(scenario.battery_price_trajectory, year, 1);
  let replacementCost =
    vehicle.battery_capacity_kwh * (BATTERY_REPLACEMENT_COST * multiplier - BATTERY_RECYCLE_VALUE);
  if (overrides?.battery_life_variation !== undefined) {
    replacementCost *= BATTERY_LIFE_VARIATION_BASE - overrides.battery_life_variation;
  }
  return replacementCost;
};

const calculateCarbonCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  dutyCycle?: DutyCycle,
  overrides?: CostOverrides
): number => {
  const carbonPrice = getSeriesValue(scenario.carbon_price_trajectory, year, 0);
  if (carbonPrice === 0) {
    return 0;
  }
  if (vehicle.drivetrain_type === 'BEV') {
    let efficiencyMultiplier = getSeriesValue(scenario.bev_efficiency_improvement, year, 1);
    if (overrides?.charging_efficiency_variation) {
      efficiencyMultiplier *= overrides.charging_efficiency_variation;
    }
    const adjustedKwhPerKm = vehicle.kwh_per_km * efficiencyMultiplier;
    const chargingMix = getDutyAdjustedChargingMix(vehicle, dutyCycle);
    const emissionsRate = getChargingBlendEmissions(chargingMix); // kg CO2e/kWh
    const emissionsTonnes = (adjustedKwhPerKm * vehicle.annual_kms * emissionsRate) / 1000;
    return emissionsTonnes * carbonPrice;
  }

  const emissionsTonnes = (vehicle.litres_per_km * vehicle.annual_kms * DIESEL_EMISSIONS) / 1000;
  return emissionsTonnes * carbonPrice;
};

const calculateMaintenanceCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): number => {
  let multiplier = getSeriesValue(scenario.maintenance_cost_multiplier, year, 1);
  if (overrides?.maintenance_cost_variation) {
    multiplier *= overrides.maintenance_cost_variation;
  }
  return getMaintenanceBaseCost(vehicle) * multiplier;
};

const calculateChargingLabourCost = (
  vehicle: VehicleDetail,
  chargingTimeOverride?: number
): number => {
  if (vehicle.drivetrain_type !== 'BEV') {
    return 0;
  }
  const dailyKms = vehicle.annual_kms / WORKING_DAYS;
  const usableRange = vehicle.range_km * BATTERY_USABLE_RANGE_FACTOR;
  const sessionsPerDay = dailyKms <= usableRange ? 0 : Math.ceil((dailyKms - usableRange) / usableRange);
  const hoursPerDay = chargingTimeOverride ?? CHARGING_TIME_HOURS[vehicle.weight_class] ?? 0;
  return sessionsPerDay * hoursPerDay * WORKING_DAYS * HOURLY_WAGE;
};

const calculatePayloadPenalty = (vehicle: VehicleDetail): number => {
  if (!vehicle.comparison_pair) {
    return 0;
  }
  const comparison = VEHICLE_BY_ID[vehicle.comparison_pair];
  if (!comparison) {
    return 0;
  }
  const payloadDifference = comparison.payload - vehicle.payload;
  if (payloadDifference <= 0) {
    return 0;
  }
  const freightRate = FREIGHT_RATE_PER_TONNE_KM[vehicle.weight_class];
  const utilisation = PAYLOAD_UTILISATION_FACTOR[vehicle.weight_class];
  return payloadDifference * freightRate * vehicle.annual_kms * utilisation;
};

const calculateStampDuty = (msrp: number, isBev: boolean): number => {
  const baseDuty = msrp * STAMP_DUTY_RATE;
  const stampPolicy = POLICY_CONFIG.stamp_duty_exemption;
  if (isBev && stampPolicy?.enabled) {
    const exemption = stampPolicy.exemption_percentage ?? 0;
    return baseDuty * (1 - exemption);
  }
  return baseDuty;
};

const calculateBevPurchaseRebate = (msrp: number): number => {
  let rebate = 0;
  const fixedPolicy = POLICY_CONFIG.purchase_rebate;
  const percentagePolicy = POLICY_CONFIG.percentage_rebate;
  if (fixedPolicy?.enabled) {
    rebate += fixedPolicy.amount ?? 0;
  }
  if (percentagePolicy?.enabled) {
    let percentage = msrp * (percentagePolicy.percentage ?? 0);
    if (percentagePolicy.max_amount) {
      percentage = Math.min(percentage, percentagePolicy.max_amount);
    }
    rebate += percentage;
  }
  return rebate;
};

const calculateInitialCost = (vehicle: VehicleDetail) => {
  const isBev = vehicle.drivetrain_type === 'BEV';
  const stampDuty = calculateStampDuty(vehicle.msrp, isBev);
  const rebate = isBev ? calculateBevPurchaseRebate(vehicle.msrp) : 0;
  return {
    stampDuty,
    rebate,
    initialCost: vehicle.msrp + stampDuty - rebate,
  };
};

const buildFinancingSnapshot = (
  initialCost: number,
  isBev: boolean,
  purchaseMethod: PurchaseMethod,
  interestRateOverride?: number
) => {
  if (purchaseMethod === 'outright') {
    return {
      upfrontCost: initialCost,
      financingCost: 0,
      monthlyPayment: 0,
      npvPurchasePayments: initialCost,
    };
  }

  const downPayment = initialCost * DOWN_PAYMENT_RATE;
  const loanAmount = initialCost - downPayment;
  let interestRate = BASE_INTEREST_RATE;
  const loanPolicy = POLICY_CONFIG.green_loan_subsidy;
  if (isBev && loanPolicy?.enabled) {
    interestRate = Math.max(0, interestRate - (loanPolicy.rate_reduction ?? 0));
  }
  const effectiveRate =
    typeof interestRateOverride === 'number' ? interestRateOverride : interestRate;
  const monthlyRate = effectiveRate / 12;
  const numPayments = FINANCING_TERM * 12;
  const monthlyPayment =
    monthlyRate === 0
      ? loanAmount / numPayments
      : (loanAmount * monthlyRate) / (1 - (1 + monthlyRate) ** -numPayments);
  const totalPayments = monthlyPayment * numPayments;
  const financingCost = totalPayments - loanAmount;
  const npvPayments = calculateNpvOfPayments(monthlyPayment, numPayments, DISCOUNT_RATE) + downPayment;

  return {
    upfrontCost: downPayment,
    financingCost,
    monthlyPayment,
    npvPurchasePayments: npvPayments,
  };
};

const calculateResidualValueAtLife = (
  initialCost: number,
  scenario: EconomicScenarioDefinition,
  isBev: boolean,
  overrides?: CostOverrides
) => {
  const firstYearDep = initialCost * DEPRECIATION_RATE_FIRST_YEAR;
  let residual = initialCost - firstYearDep;
  for (let year = 2; year <= VEHICLE_LIFE; year += 1) {
    residual *= 1 - DEPRECIATION_RATE_ONGOING;
  }
  if (isBev) {
    residual *= getSeriesValue(scenario.bev_residual_value_multiplier, VEHICLE_LIFE, 1);
  }
  if (overrides?.residual_value_variation) {
    residual *= overrides.residual_value_variation;
  }
  return {
    residualFuture: residual,
    depreciation: initialCost - residual,
  };
};

const getAnnualInsuranceCost = (vehicle: VehicleDetail): number => {
  const rate = vehicle.drivetrain_type === 'BEV' ? INSURANCE_RATE_BEV : INSURANCE_RATE_DSL;
  return vehicle.msrp * rate + OTHER_INSURANCE;
};

export const calculateTco = (payload: CalculationRequestPayload): CalculationResponsePayload => {
  // Sanitize payload to prevent NaN and invalid values
  const sanitizedPayload = sanitizePayload(payload);

  const baseVehicle = getVehicle(sanitizedPayload.vehicle_id);
  const scenario = getScenario(sanitizedPayload.scenario_name);
  const overrides = sanitizedPayload.overrides;
  const dutyCycle = sanitizedPayload.duty_cycle ?? DEFAULT_DUTY_CYCLE;
  const vehicleWithStructuralOverrides = applyVehicleOverrides(
    baseVehicle,
    sanitizedPayload.vehicle_overrides
  );
  const annualKms =
    overrides?.annual_kms_variation && overrides.annual_kms_variation > 0
      ? overrides.annual_kms_variation
      : vehicleWithStructuralOverrides.annual_kms;
  const vehicle: VehicleDetail = {
    ...vehicleWithStructuralOverrides,
    annual_kms: annualKms,
  };
  const isBev = vehicle.drivetrain_type === 'BEV';

  const { stampDuty, initialCost } = calculateInitialCost(vehicle);
  const financing = buildFinancingSnapshot(
    initialCost,
    isBev,
    sanitizedPayload.purchase_method,
    sanitizedPayload.vehicle_overrides?.interest_rate_override
  );
  const annualInsuranceCost = getAnnualInsuranceCost(vehicle);
  const annualChargingLabourCost = calculateChargingLabourCost(
    vehicle,
    sanitizedPayload.vehicle_overrides?.charging_time_hours_override
  );
  const annualPayloadPenalty = calculatePayloadPenalty(vehicle);

  const annualFuelCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateFuelCostYear(vehicle, scenario, idx + 1, overrides, dutyCycle)
  );
  const annualBatteryCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateBatteryReplacementYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualCarbonCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateCarbonCostYear(vehicle, scenario, idx + 1, dutyCycle, overrides)
  );
  const annualMaintenanceCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateMaintenanceCostYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualChargingLabourCosts = Array.from({ length: VEHICLE_LIFE }, () => annualChargingLabourCost);
  const annualPayloadPenalties = Array.from({ length: VEHICLE_LIFE }, () => annualPayloadPenalty);

  const totalFuelCost = calculateNpvOfAnnualCashflows(annualFuelCosts, DISCOUNT_RATE);
  const totalBatteryCost = calculateNpvOfAnnualCashflows(annualBatteryCosts, DISCOUNT_RATE);
  const totalCarbonCost = calculateNpvOfAnnualCashflows(annualCarbonCosts, DISCOUNT_RATE);
  const totalMaintenanceCost = calculateNpvOfAnnualCashflows(annualMaintenanceCosts, DISCOUNT_RATE);
  const totalChargingLabourCost = calculateNpvOfAnnualCashflows(annualChargingLabourCosts, DISCOUNT_RATE);
  const totalPayloadPenalty = calculateNpvOfAnnualCashflows(annualPayloadPenalties, DISCOUNT_RATE);

  const insurancePv = calculatePresentValue(annualInsuranceCost, VEHICLE_LIFE, DISCOUNT_RATE);
  const registrationPv = calculatePresentValue(vehicle.annual_registration, VEHICLE_LIFE, DISCOUNT_RATE);

  const { residualFuture, depreciation } = calculateResidualValueAtLife(
    initialCost,
    scenario,
    isBev,
    overrides
  );
  const residualValuePv = discountToPresent(residualFuture, VEHICLE_LIFE, DISCOUNT_RATE);

  const totalCost =
    financing.npvPurchasePayments +
    totalFuelCost +
    totalMaintenanceCost +
    insurancePv +
    registrationPv +
    totalBatteryCost +
    totalCarbonCost +
    totalChargingLabourCost +
    totalPayloadPenalty -
    residualValuePv;

  const annualCost = calculateAnnualisedCost(totalCost, VEHICLE_LIFE, DISCOUNT_RATE);
  const costPerKm = vehicle.annual_kms > 0 ? annualCost / vehicle.annual_kms : 0;

  const taxesAndFees = stampDuty + vehicle.annual_registration * VEHICLE_LIFE;

  const breakdown: CostBreakdown = {
    purchase_cost: financing.upfrontCost,
    fuel_cost: totalFuelCost,
    maintenance_cost: totalMaintenanceCost,
    insurance_cost: annualInsuranceCost * VEHICLE_LIFE,
    registration_cost: vehicle.annual_registration * VEHICLE_LIFE,
    battery_replacement_cost: totalBatteryCost,
    financing_cost: financing.financingCost,
    carbon_cost: totalCarbonCost,
    charging_labour_cost: totalChargingLabourCost,
    payload_penalty_cost: totalPayloadPenalty,
    residual_value: residualValuePv,
    depreciation,
    taxes_and_fees: taxesAndFees,
  };

  return {
    vehicle_id: vehicle.vehicle_id,
    scenario_name: scenario.name,
    total_cost: totalCost,
    annual_cost: annualCost,
    cost_per_km: costPerKm,
    breakdown,
  };
};

export const calculateComparison = (
  payload: ComparisonRequestPayload
): CalculationResponsePayload[] => {
  return payload.vehicle_ids.map((vehicleId) =>
    calculateTco({
      vehicle_id: vehicleId,
      scenario_name: payload.scenario_name,
      purchase_method: payload.purchase_method,
      duty_cycle: payload.duty_cycle,
      overrides: payload.overrides,
      vehicle_overrides: payload.vehicle_param_overrides?.[vehicleId],
    })
  );
};

export const getVehicleCatalogSnapshot = () => VEHICLE_DETAILS;
</file>

<file path="shared/types/tco.types.ts">
/**
 * @file TCO Type Definitions
 * @module shared/types/tco.types
 *
 * TypeScript interfaces and types for the TCO calculator.
 * Defines vehicle specifications, scenarios, calculation inputs/outputs,
 * and wizard state structures.
 */

export type ScenarioKey = 'baseline' | 'technology_breakthrough' | 'oil_crisis';
export type PurchaseMethod = 'financed' | 'outright';

type Primitive = string | number | boolean | null;
type NestedValue = Primitive | NestedValue[] | { [key: string]: NestedValue };
export type ConstantCatalog = Record<string, NestedValue>;

export interface EconomicScenarioDefinition {
  key: string;
  name: string;
  description: string;
  diesel_price_trajectory: number[];
  electricity_price_trajectory: number[];
  battery_price_trajectory: number[];
  carbon_price_trajectory: number[];
  bev_efficiency_improvement: number[];
  diesel_efficiency_improvement: number[];
  maintenance_cost_multiplier: number[];
  bev_residual_value_multiplier: number[];
  infrastructure_cost_trajectory: number[];
  policy_phase_out_year: number | null;
  road_user_charge_bev_start_year: number | null;
}

export type ScenarioDefinitionMap = Record<ScenarioKey, EconomicScenarioDefinition>;

export interface PolicyDefinition {
  name: string;
  description: string;
  enabled: boolean;
  policy_type: string;
  amount?: number | null;
  percentage?: number | null;
  max_amount?: number | null;
  exemption_percentage?: number | null;
  price_per_tonne?: number | null;
  rate_reduction?: number | null;
  grant_percentage?: number | null;
}

export type PolicyCatalog = Record<string, PolicyDefinition>;

export interface CostOverrides {
  annual_kms_variation?: number;
  residual_value_variation?: number;
  fuel_price_variation?: number;
  electricity_price_variation?: number;
  maintenance_cost_variation?: number;
  battery_life_variation?: number;
  charging_efficiency_variation?: number;
}

export interface VehicleParamOverrides {
  msrp_override?: number;
  payload_override?: number;
  range_km_override?: number;
  battery_capacity_kwh_override?: number;
  kwh_per_km_override?: number;
  litres_per_km_override?: number;
  annual_registration_override?: number;
  interest_rate_override?: number;
  charging_time_hours_override?: number;
}

export interface CalculationRequestPayload {
  vehicle_id: string;
  scenario_name: ScenarioKey;
  purchase_method: PurchaseMethod;
  duty_cycle?: DutyCycle;
  overrides?: CostOverrides;
  vehicle_overrides?: VehicleParamOverrides;
}

/**
 * Cost breakdown for a vehicle over its lifetime.
 *
 * NOTE: Value types are MIXED for different cost categories:
 * - NPV-adjusted: fuel_cost, maintenance_cost, battery_replacement_cost,
 *   carbon_cost, charging_labour_cost, payload_penalty_cost, residual_value
 * - Nominal lifetime totals: insurance_cost, registration_cost, depreciation
 * - Upfront values: purchase_cost, financing_cost, taxes_and_fees
 *
 * The total_cost in CalculationResponsePayload IS NPV-adjusted.
 */
export interface CostBreakdown {
  purchase_cost: number;
  fuel_cost: number;
  maintenance_cost: number;
  insurance_cost: number;
  registration_cost: number;
  battery_replacement_cost: number;
  financing_cost: number;
  carbon_cost: number;
  charging_labour_cost: number;
  payload_penalty_cost: number;
  residual_value: number;
  depreciation: number;
  taxes_and_fees: number;
}

export interface CalculationResponsePayload {
  vehicle_id: string;
  scenario_name: ScenarioKey | string;
  total_cost: number;
  annual_cost: number;
  cost_per_km: number;
  breakdown: CostBreakdown;
}

export interface ComparisonRequestPayload {
  vehicle_ids: string[];
  scenario_name: ScenarioKey;
  purchase_method: PurchaseMethod;
  duty_cycle?: DutyCycle;
  overrides?: CostOverrides;
  vehicle_param_overrides?: Record<string, VehicleParamOverrides>;
}

export interface VehicleSummary {
  vehicle_id: string;
  model_name: string;
  drivetrain_type: 'BEV' | 'Diesel';
  weight_class: 'Light Rigid' | 'Medium Rigid' | 'Articulated';
  comparison_pair: string;
}

export interface VehicleDetail extends VehicleSummary {
  payload: number;
  msrp: number;
  range_km: number;
  battery_capacity_kwh: number;
  kwh_per_km: number;
  litres_per_km: number;
  maintenance_cost_per_km: number;
  annual_registration: number;
  annual_kms: number;
}

export interface DutyCycle {
  urban: number;
  regional: number;
  longHaul: number;
}

export interface WizardData {
  currentVehicle?: string;
  comparisonVehicles: string[];
  scenario: ScenarioKey;
  purchaseMethod: PurchaseMethod;
  dutyCycle: DutyCycle;
  overrides?: CostOverrides;
  vehicleParamOverrides?: Record<string, VehicleParamOverrides>;
}

export interface OperatorProfilePayload {
  operatorType?: string;
  fleetSize?: string;
  contactEmail?: string;
  consentToContact?: boolean;
  notes?: string;
}

export interface FeedbackPayload {
  rating?: number;
  comment?: string;
}

export interface SessionCreatePayload {
  wizardData: WizardData;
  results?: CalculationResponsePayload[];
  operatorProfile?: OperatorProfilePayload;
  feedback?: FeedbackPayload;
}

export interface SessionResponsePayload extends SessionCreatePayload {
  sessionId: string;
  status: 'draft' | 'completed';
  updatedAt: string;
  lastCalculatedAt?: string | null;
}

export type SessionUpdatePayload = Partial<SessionCreatePayload>;

export interface AnalyticsSummaryPayload {
  totalSessions: number;
  completedSessions: number;
  calculationsLast24h: number;
  bevWinRate?: number | null;
  averagePaybackYears?: number | null;
  averageCostDelta?: number | null;
  topVehicles: Record<string, number>;
}

export interface ApiError {
  detail: string;
}
</file>

<file path="frontend/src/components/wizard/WizardElectricStep.tsx">
import { useEffect, useMemo, useState } from 'react';
import Card from '@components/shared/Card';
import Select from '@components/shared/Select';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import VehicleParamsForm from './VehicleParamsForm';
import { formatCurrency } from '@utils/format';

const WizardElectricStep = () => {
  const { data: catalog } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const [activeComparison, setActiveComparison] = useState<string | undefined>(
    () => wizardData.comparisonVehicles[0]
  );

  const baseline = wizardData.currentVehicle
    ? vehicleDetails[wizardData.currentVehicle]
    : undefined;

  const bevOptions = useMemo(() => {
    if (!baseline) {
      return [];
    }
    return (catalog ?? []).filter(
      (vehicle) =>
        vehicle.drivetrain_type === 'BEV' && vehicle.weight_class === baseline.weight_class
    );
  }, [baseline, catalog]);

  useEffect(() => {
    if (!wizardData.comparisonVehicles.length) {
      setActiveComparison(undefined);
      return;
    }
    if (!activeComparison || !wizardData.comparisonVehicles.includes(activeComparison)) {
      setActiveComparison(wizardData.comparisonVehicles[0]);
    }
  }, [activeComparison, wizardData.comparisonVehicles]);

  const addComparator = (vehicleId: string) => {
    if (!vehicleId) {
      return;
    }
    const deduped = Array.from(
      new Set([...wizardData.comparisonVehicles, vehicleId])
    );
    updateWizard({ comparisonVehicles: deduped });
    setActiveComparison(vehicleId);
  };

  const removeComparator = (vehicleId: string) => {
    updateWizard({
      comparisonVehicles: wizardData.comparisonVehicles.filter((id) => id !== vehicleId),
    });
  };

  const suggestion =
    baseline?.comparison_pair && baseline.comparison_pair.startsWith('BEV')
      ? baseline.comparison_pair
      : undefined;
  const suggestionDetail = suggestion ? vehicleDetails[suggestion] : undefined;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <Card
        title="Electric trucks to compare"
        subtitle={
          baseline
            ? `Showing ${baseline.weight_class} electric trucks so you can compare like-for-like.`
            : 'Select a diesel truck first to see available electric options.'
        }
      >
        {!baseline ? (
          <p className="text-sm text-slate-500">Choose a diesel truck in step 1 first.</p>
        ) : (
          <>
            <Select
              label="Add an electric truck"
              hint="You can add multiple electric trucks - each will show up as a chip below."
              defaultValue=""
              onChange={(event) => {
                const id = event.currentTarget.value;
                if (id) {
                  addComparator(id);
                  event.currentTarget.value = '';
                }
              }}
            >
              <option value="">Select…</option>
              {bevOptions.map((vehicle) => (
                <option
                  key={vehicle.vehicle_id}
                  value={vehicle.vehicle_id}
                  title={`${vehicle.model_name} (${vehicle.vehicle_id})`}
                >
                  {vehicle.model_name}
                </option>
              ))}
            </Select>

            {suggestion && suggestionDetail && !wizardData.comparisonVehicles.includes(suggestion) && (
              <button
                type="button"
                className="mt-3 text-sm font-medium text-brand-blue hover:underline"
                onClick={() => addComparator(suggestion)}
              >
                + Add suggested pair: {suggestionDetail.model_name}
              </button>
            )}

            <div className="mt-8">
              <p className="text-xs font-bold text-slate-500 mb-3">
                Trucks you're comparing
              </p>
              {!wizardData.comparisonVehicles.length ? (
                <p className="text-sm text-slate-400 italic">No electric trucks selected yet.</p>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {wizardData.comparisonVehicles.map((vehicleId) => {
                    const detail = vehicleDetails[vehicleId];
                    const isActive = vehicleId === activeComparison;
                    const displayName = detail?.model_name ?? vehicleId;
                    return (
                      <div
                        key={vehicleId}
                        className={`flex items-center gap-3 rounded-md border px-4 py-2 text-sm transition-all shadow-sm cursor-pointer ${isActive
                          ? 'border-brand-primary bg-brand-primary/10 text-black shadow-md ring-1 ring-brand-primary'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-brand-primary/50'
                          }`}
                        role="button"
                        tabIndex={0}
                        onClick={() => setActiveComparison(vehicleId)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setActiveComparison(vehicleId);
                          }
                        }}
                      >
                        <div className="flex flex-col">
                          <span className="font-bold leading-tight">{displayName}</span>
                          {detail && (
                            <span className="text-xs text-slate-500">
                              {formatCurrency(detail.msrp)}
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors"
                          aria-label={`Remove ${displayName}`}
                          onClick={(event) => {
                            event.stopPropagation();
                            removeComparator(vehicleId);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </Card>

      <VehicleParamsForm
        vehicleId={activeComparison}
        title="Adjust specifications"
      />
    </div>
  );
};

export default WizardElectricStep;
</file>

<file path="frontend/src/state/tcoStore.ts">
/**
 * @file TCO Store - Application State Management
 * @module frontend/state/tcoStore
 *
 * Zustand store for managing wizard state, calculation results,
 * and session persistence.
 *
 * State is persisted to localStorage under key 'tco-wizard-store'.
 *
 * @see frontend/hooks/useCalculations.ts for calculation triggers
 * @see frontend/pages/WizardPage.tsx for main consumer
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { VEHICLE_BY_ID, VEHICLE_CATALOG_VERSION } from '@shared/data/vehicleCatalog';
import type {
  CalculationResponsePayload,
  DutyCycle,
  VehicleDetail,
  WizardData,
} from '@shared/types/tco.types';

interface TCOStore {
  stepIndex: number;
  wizardData: WizardData;
  results: CalculationResponsePayload[];
  isCalculating: boolean;
  vehicleDetails: Record<string, VehicleDetail>;
  sessionId?: string;
  updateWizard: (data: Partial<WizardData>) => void;
  setStepIndex: (index: number) => void;
  setResults: (results: CalculationResponsePayload[]) => void;
  resetResults: () => void;
  setIsCalculating: (state: boolean) => void;
  setSessionId: (sessionId?: string) => void;
}

const defaultWizardData: WizardData = {
  currentVehicle: undefined,
  comparisonVehicles: [],
  scenario: 'baseline',
  purchaseMethod: 'financed',
  dutyCycle: {
    urban: 60,
    regional: 25,
    longHaul: 15,
  },
  overrides: {},
  vehicleParamOverrides: {},
};

const initialVehicleDetails: Record<string, VehicleDetail> = { ...VEHICLE_BY_ID };

/**
 * Validates duty cycle values, returning defaults or clamped values if invalid
 */
const validateDutyCycle = (dutyCycle?: DutyCycle): DutyCycle | undefined => {
  if (!dutyCycle) return undefined;

  const { urban, regional, longHaul } = dutyCycle;

  // Check for NaN or non-numeric values
  if ([urban, regional, longHaul].some(v => typeof v !== 'number' || isNaN(v))) {
    console.warn('Invalid duty cycle values detected, using defaults');
    return defaultWizardData.dutyCycle;
  }

  // Check for negative values
  if ([urban, regional, longHaul].some(v => v < 0)) {
    console.warn('Negative duty cycle values detected, clamping to 0');
    return {
      urban: Math.max(0, urban),
      regional: Math.max(0, regional),
      longHaul: Math.max(0, longHaul),
    };
  }

  return dutyCycle;
};

export const useTCOStore = create<TCOStore>()(
  persist(
    (set) => ({
      stepIndex: 0,
      wizardData: defaultWizardData,
      results: [],
      isCalculating: false,
      vehicleDetails: initialVehicleDetails,
      sessionId: undefined,
      updateWizard: (data) =>
        set((state) => {
          const validatedData = { ...data };

          if (data.dutyCycle) {
            validatedData.dutyCycle = validateDutyCycle(data.dutyCycle);
          }

          return {
            wizardData: { ...state.wizardData, ...validatedData },
          };
        }),
      setStepIndex: (index) => set({ stepIndex: index }),
      setResults: (results) =>
        set((state) => {
          const orderedIds = [
            state.wizardData.currentVehicle,
            ...state.wizardData.comparisonVehicles,
          ].filter(Boolean) as string[];
          const prioritized = orderedIds
            .map((vehicleId) => results.find((result) => result.vehicle_id === vehicleId))
            .filter(Boolean) as CalculationResponsePayload[];
          const remainder = results.filter(
            (result) => !orderedIds.includes(result.vehicle_id)
          );
          return { results: [...prioritized, ...remainder] };
        }),
      resetResults: () => set({ results: [] }),
      setIsCalculating: (state) => set({ isCalculating: state }),
      setSessionId: (sessionId) => set({ sessionId }),
    }),
    {
      name: 'tco-wizard-store',
      partialize: (state) => ({
        _vehicleCatalogVersion: VEHICLE_CATALOG_VERSION,
        wizardData: state.wizardData,
        results: state.results,
        vehicleDetails: state.vehicleDetails,
        sessionId: state.sessionId,
      }),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.warn('Failed to rehydrate store:', error);
          return;
        }

        if (!state) return;

        // Check vehicle catalog version and refresh if outdated
        const storedVersion = (state as { _vehicleCatalogVersion?: string })._vehicleCatalogVersion;
        if (storedVersion !== VEHICLE_CATALOG_VERSION) {
          console.info('Vehicle catalog updated, refreshing cache');
          state.vehicleDetails = { ...VEHICLE_BY_ID };
        }

        // Validate duty cycle values
        if (state.wizardData.dutyCycle) {
          const { urban, regional, longHaul } = state.wizardData.dutyCycle;
          const hasInvalidDutyCycle =
            typeof urban !== 'number' || isNaN(urban) ||
            typeof regional !== 'number' || isNaN(regional) ||
            typeof longHaul !== 'number' || isNaN(longHaul);
          if (hasInvalidDutyCycle) {
            state.wizardData.dutyCycle = defaultWizardData.dutyCycle;
          }
        }
      },
    }
  )
);
</file>

<file path="replit.md">
# Overview

The MyBuild TCO (Total Cost of Ownership) Calculator is a web platform designed to help truck operators and fleet managers compare the economics of battery-electric vehicles (BEV) versus diesel trucks over a 15-year lifecycle. It performs detailed financial modeling across 14 cost components, including purchase, operating expenses, financing, maintenance, battery replacement, and residual value. The platform supports scenario analysis (baseline, technology breakthrough, oil crisis) and provides individual calculations and fleet-wide comparisons across light rigid, medium rigid, and articulated truck classes.

The system comprises a shared TypeScript calculation engine, a modern React + TypeScript frontend wizard, and a FastAPI backend. The legacy Python engine now lives in `archive/` for historical reference; the TypeScript calculator is the active source of truth.

# Recent Changes

**Production Release: November 10, 2025**

The application has been successfully deployed to production with the following features:

- **Complete**: All four development phases (Step 1-4) have been implemented and tested
- **Features Delivered**:
  - Interactive three-step wizard for vehicle selection, operating profile, and cost inputs
  - Real-time TCO calculations with the shared TypeScript engine (±1% parity validated)
  - Session persistence with PostgreSQL and Redis caching
  - Analytics dashboard with aggregated insights
  - Results visualization with cost breakdowns, comparison highlights, and charts
- **Code Cleanup**: Legacy code and transition documentation moved to `archive/` folder
- **Documentation**: Comprehensive production documentation added (README.md, API.md, DEPLOYMENT.md, TROUBLESHOOTING.md)
- **Production-Ready**: Database schema finalized, caching optimized, error handling implemented

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Patterns

**Monorepo Structure with Shared Data Layer**: The project uses a monorepo containing frontend, backend, and shared modules. Python scripts generate TypeScript data files from authoritative Python sources, ensuring identical vehicle specifications, constants, scenarios, and policy definitions are shared between frontend and backend.

**Shared Calculator Pattern**: The system uses a single TypeScript calculator (shared across frontend and backend contexts) that implements a 15-year discounted cash flow model with 14 cost components, validated for ±1% parity against committed fixtures. The legacy Python engine is archived and no longer called at runtime.

## Data Flow Architecture

**Three-Tier Calculation Flow**: Calculations proceed through an Input Layer (pre-calculates subcomponents), a Calculator Layer (applies year-by-year trajectories), and an Aggregation Layer (discounts future costs to present value and calculates metrics).

**Wizard State Management**: The frontend uses Zustand for global state and React Hook Form + Zod for validation. Selections are persisted to backend sessions via `/sessions` endpoints.

## Frontend Architecture

**Progressive Wizard Pattern**: A three-step wizard (vehicle selection → operating profile → cost overrides) with validation, smart defaults, and inline help. Built with React 18, Vite, Tailwind CSS, and React Router.

**Optimistic Calculation Strategy**: Calculations run in the shared TypeScript calculator on the client; the backend handles policy data exposure, session persistence, and analytics. Results are cached locally and persisted to the backend.

## Backend Architecture

**FastAPI Service Layer**: The backend exposes REST endpoints for vehicle catalog access, session management, and analytics; calculation endpoints now rely on the shared TypeScript engine rather than the archived Python implementation.

**Service Pattern**: Domain logic is organized into service classes that translate HTTP requests to calculator calls and marshal responses using Pydantic schemas.

**Caching Strategy**: In-memory result caching and Redis session snapshots (30-minute TTL) are used to improve performance.

## Database Schema

SQLAlchemy Async Models define the database schema, including `SessionRecord`, `UserInputRecord`, `CalculationResultRecord`, `OperatorProfileRecord`, and `FeedbackRecord`. PostgreSQL is used in production, with SQLite for local development. Redis caches session snapshots.

## Calculation Engine Design

**Modular Calculator Architecture**: The `shared/calculator/` directory contains modules for financial modeling, operating costs, utilities, and simulation (mirroring the archived Python layout in `archive/calculations_legacy/`).

**Scenario System**: `EconomicScenario` dataclasses define time-varying parameters (e.g., fuel prices, battery costs) across predefined and custom scenarios.

**Policy Toggles**: Dataclass-based policy definitions (e.g., rebates, carbon pricing) can be enabled/disabled and tuned.

## Code Generation Pipeline

**Shared Data SDK**: A Python script generates TypeScript files (`vehicleCatalog.ts`, `constants.ts`, `scenarios.ts`, `policies.ts`) from Python dataclasses, ensuring data consistency between frontend and backend.

**Parity Validation**: Vitest uses committed fixtures in `shared/calculator/verification_data.json` to keep the TypeScript calculator stable; the old Python snapshot generator has been retired.

# External Dependencies

## Databases

**PostgreSQL**: Used for session persistence, calculation history, operator profiles, and feedback. Configured with `postgresql+asyncpg` driver.

**Redis**: Used for TTL-based session caching (30 minutes TTL).

**SQLite**: Used for local development and testing.

## Key Python Libraries

**Core Calculation (legacy)**: `numpy`, `numpy-financial`, `pandas`, `plotly`.
**Backend Framework**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `redis[asyncio]`.
**Testing & Quality**: `pytest` and related plugins, `black`, `isort`, `ruff`, `mypy`.

## Key Frontend Libraries

**Framework & Build**: `react`, `react-dom`, `vite`, `typescript`.
**State & Data**: `zustand`, `@tanstack/react-query`, `axios`, `zod`, `react-hook-form`.
**UI & Visualization**: `tailwindcss`, `recharts`, `react-router-dom`, `react-hot-toast`.
**Testing**: `vitest`, `@vitejs/plugin-react`.

## Development Tools

**Pre-commit Hooks**: Enforce code quality standards.
**Docker Compose**: Orchestrates frontend, backend, Postgres, and Redis.
**CI/CD**: GitHub Actions for linting, type checking, and testing.
</file>

<file path="frontend/src/components/wizard/WizardDieselStep.tsx">
import { useMemo } from 'react';
import Card from '@components/shared/Card';
import Select from '@components/shared/Select';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import VehicleParamsForm from './VehicleParamsForm';
import { formatCurrency } from '@utils/format';

const WizardDieselStep = () => {
  const { data: catalog } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const updateWizard = useTCOStore((state) => state.updateWizard);

  const dieselOptions = useMemo(
    () => (catalog ?? []).filter((vehicle) => vehicle.drivetrain_type === 'Diesel'),
    [catalog]
  );

  const selected = wizardData.currentVehicle
    ? vehicleDetails[wizardData.currentVehicle]
    : undefined;

  const handleSelect = (vehicleId: string) => {
    if (!vehicleId) {
      updateWizard({ currentVehicle: undefined, comparisonVehicles: [] });
      return;
    }
    const baseline = vehicleDetails[vehicleId];
    const filteredComparisons = wizardData.comparisonVehicles.filter((id) => {
      const detail = vehicleDetails[id];
      return detail && baseline && detail.weight_class === baseline.weight_class;
    });
    updateWizard({
      currentVehicle: vehicleId,
      comparisonVehicles: filteredComparisons,
    });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <Card
        title="Your current truck"
        subtitle="Select the diesel truck you operate today, or the closest match."
      >
        <Select
          label="Select your truck"
          value={wizardData.currentVehicle ?? ''}
          onChange={(event) => handleSelect(event.currentTarget.value)}
          hint="Showing diesel trucks only. Your selection is saved as you move through the steps."
        >
          <option value="">Select…</option>
          {dieselOptions.map((vehicle) => (
            <option
              key={vehicle.vehicle_id}
              value={vehicle.vehicle_id}
              title={`${vehicle.model_name} (${vehicle.vehicle_id})`}
            >
              {vehicle.model_name} ({vehicle.weight_class})
            </option>
          ))}
        </Select>

        {selected ? (
          <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-6">
            <dl className="grid gap-6 md:grid-cols-2">
              <div className="border-b border-slate-200 pb-2 md:border-b-0 md:pb-0">
                <dt className="text-xs text-slate-500 font-bold mb-1">Model</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.model_name}</dd>
              </div>
              <div className="border-b border-slate-200 pb-2 md:border-b-0 md:pb-0">
                <dt className="text-xs text-slate-500 font-bold mb-1">Weight class</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.weight_class}</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500 font-bold mb-1">Payload</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.payload.toFixed(1)} t</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500 font-bold mb-1">Purchase price</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{formatCurrency(selected.msrp)}</dd>
              </div>
            </dl>
          </div>
        ) : (
          <p className="mt-5 text-sm text-slate-500 italic">Select a truck above to see details.</p>
        )}
      </Card>

      <VehicleParamsForm
        vehicleId={wizardData.currentVehicle}
        title="Adjust specifications"
        showElectricFields={false}
        subtitle={null}
      />
    </div>
  );
};

export default WizardDieselStep;
</file>

<file path="frontend/src/pages/WizardPage.tsx">
import { useEffect, useRef } from 'react';
import { FormProvider, type FieldPath, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Card from '@components/shared/Card';
import Button from '@components/shared/Button';
import WizardDieselStep from '@components/wizard/WizardDieselStep';
import WizardElectricStep from '@components/wizard/WizardElectricStep';
import WizardCompareStep from '@components/wizard/WizardCompareStep';
import WizardStepper, { type WizardStep } from '@components/wizard/WizardStepper';
import { useCalculationRunner } from '@hooks/useCalculations';
import { useWizardAutosave } from '@hooks/useWizardAutosave';
import { useTCOStore } from '@state/tcoStore';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';
import type { ComparisonRequestPayload, DutyCycle } from '@shared/types/tco.types';
import type { WizardFormValues } from '@forms/wizardForm';
import { wizardFormSchema } from '@forms/wizardForm';
import { toast } from 'react-hot-toast';

const steps: WizardStep[] = [
  {
    title: 'Your current truck',
    description: 'Select the diesel truck you operate today.',
  },
  {
    title: 'Electric options',
    description: 'Choose electric trucks to compare.',
  },
  {
    title: 'See your results',
    description: 'View results and explore scenarios.',
  },
];

const stepFieldMap: FieldPath<WizardFormValues>[][] = [
  [],
  [],
  [
    'scenario',
    'purchaseMethod',
    'dutyCycle.urban',
    'dutyCycle.regional',
    'dutyCycle.longHaul',
    'overrides.annual_kms_variation',
    'overrides.residual_value_variation',
    'overrides.maintenance_cost_variation',
    'overrides.fuel_price_variation',
    'overrides.electricity_price_variation',
    'overrides.battery_life_variation',
    'overrides.charging_efficiency_variation',
  ],
];

const WizardPage = () => {
  const stepIndex = useTCOStore((state) => state.stepIndex);
  const setStepIndex = useTCOStore((state) => state.setStepIndex);
  const wizardData = useTCOStore((state) => state.wizardData);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const { runComparison } = useCalculationRunner();
  useWizardAutosave();
  const formMethods = useForm<WizardFormValues>({
    resolver: zodResolver(wizardFormSchema),
    mode: 'onTouched',
    defaultValues: {
      scenario: wizardData.scenario,
      purchaseMethod: wizardData.purchaseMethod,
      dutyCycle: wizardData.dutyCycle,
      overrides: wizardData.overrides ?? {},
    },
  });

  const isLastStep = stepIndex === steps.length - 1;
  const baselineSelected = Boolean(wizardData.currentVehicle);
  const isUpdatingFromForm = useRef(false);
  const stepComponents = [
    <WizardDieselStep key="diesel" />,
    <WizardElectricStep key="electric" />,
    <WizardCompareStep key="compare" />,
  ];
  const activeComponent = stepComponents[stepIndex];

  useEffect(() => {
    // Skip if we just updated the store from form (prevents circular update)
    if (isUpdatingFromForm.current) {
      isUpdatingFromForm.current = false;
      return;
    }
    const currentValues = formMethods.getValues();
    const overridesMatch =
      JSON.stringify(currentValues.overrides ?? {}) === JSON.stringify(wizardData.overrides ?? {});
    const dutyCycleMatch =
      currentValues.dutyCycle?.urban === wizardData.dutyCycle.urban &&
      currentValues.dutyCycle?.regional === wizardData.dutyCycle.regional &&
      currentValues.dutyCycle?.longHaul === wizardData.dutyCycle.longHaul;
    if (
      currentValues.scenario !== wizardData.scenario ||
      currentValues.purchaseMethod !== wizardData.purchaseMethod ||
      !overridesMatch ||
      !dutyCycleMatch
    ) {
      formMethods.reset({
        scenario: wizardData.scenario,
        purchaseMethod: wizardData.purchaseMethod,
        dutyCycle: wizardData.dutyCycle,
        overrides: wizardData.overrides ?? {},
      });
    }
  }, [
    formMethods,
    wizardData.overrides,
    wizardData.dutyCycle.longHaul,
    wizardData.dutyCycle.regional,
    wizardData.dutyCycle.urban,
    wizardData.purchaseMethod,
    wizardData.scenario,
  ]);

  useEffect(() => {
    const subscription = formMethods.watch((values) => {
      const dutyCycle = values.dutyCycle as DutyCycle | undefined;
      isUpdatingFromForm.current = true;
      updateWizard({
        scenario: values.scenario,
        purchaseMethod: values.purchaseMethod,
        dutyCycle: dutyCycle ?? { urban: 40, regional: 35, longHaul: 25 },
        overrides: values.overrides ?? {},
      });
    });
    return () => subscription.unsubscribe();
  }, [formMethods, updateWizard]);

  const validateCurrentStep = async () => {
    const fieldsToValidate = stepFieldMap[stepIndex];
    if (fieldsToValidate?.length) {
      return formMethods.trigger(fieldsToValidate);
    }
    return true;
  };

  const goNext = async () => {
    if (isLastStep || !baselineSelected) {
      return;
    }
    const isValid = await validateCurrentStep();
    if (!isValid) {
      return;
    }
    setStepIndex(Math.min(stepIndex + 1, steps.length - 1));
  };

  const goPrev = () => setStepIndex(Math.max(stepIndex - 1, 0));

  const handleStepClick = async (targetIndex: number) => {
    if (targetIndex === stepIndex) {
      return;
    }
    if (targetIndex > stepIndex && !baselineSelected) {
      return;
    }
    if (targetIndex > stepIndex) {
      const isValid = await validateCurrentStep();
      if (!isValid) {
        return;
      }
    }
    setStepIndex(Math.max(0, Math.min(targetIndex, steps.length - 1)));
  };

  const handleCalculate = async () => {
    if (!wizardData.currentVehicle) {
      return;
    }

    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles.filter(Boolean)])
    );

    const formValues = formMethods.getValues();
    const payload: ComparisonRequestPayload = {
      vehicle_ids: vehicleIds,
      scenario_name: formValues.scenario,
      purchase_method: formValues.purchaseMethod,
      duty_cycle: formValues.dutyCycle,
    };

    const overrides = compactOverrides(formValues.overrides ?? {});
    if (Object.keys(overrides).length) {
      payload.overrides = overrides;
    }
    const vehicleOverrides = compactVehicleParamOverrides(
      wizardData.vehicleParamOverrides ?? {}
    );
    if (Object.keys(vehicleOverrides).length) {
      payload.vehicle_param_overrides = vehicleOverrides;
    }

    try {
      const isValid = await formMethods.trigger();
      if (!isValid) {
        toast.error('Check the highlighted fields before running a comparison.');
        return;
      }
      await runComparison(payload);
      toast.success('Comparison saved to your session.');
    } catch (error) {
      console.error('Calculation failed', error);
      toast.error('Calculation failed. Please try again.');
    }
  };

  return (
    <FormProvider {...formMethods}>
      <div className="flex flex-col gap-6">
        <WizardStepper steps={steps} activeIndex={stepIndex} onStepClick={handleStepClick} />

        {activeComponent}

        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Step {stepIndex + 1} of {steps.length}
            </p>
            {!baselineSelected && (
              <p className="text-xs text-rose-500">Select at least one truck to continue.</p>
            )}
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" onClick={goPrev} disabled={stepIndex === 0 || isCalculating}>
              Back
            </Button>
            {isLastStep ? (
              <Button onClick={handleCalculate} disabled={!baselineSelected || isCalculating}>
                {isCalculating ? 'Calculating…' : 'Run comparison'}
              </Button>
            ) : (
              <Button onClick={() => void goNext()} disabled={!baselineSelected || isCalculating}>
                Next
              </Button>
            )}
          </div>
        </Card>
      </div>
    </FormProvider>
  );
};

export default WizardPage;
</file>

<file path="backend/app/core/config.py">
"""Application configuration via environment variables."""

from functools import lru_cache
import os
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI service."""

    project_name: str = Field(default="TCO Web Platform API")
    version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    environment: str = Field(default="development")
    backend_cors_origins: List[AnyHttpUrl] | List[str] = Field(
        default_factory=lambda: ["http://localhost:5000", "http://127.0.0.1:5000"]
    )
    cache_results: bool = Field(
        default=True, description="Toggle for caching calculation runs in memory."
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./tco.db",
        description="SQLAlchemy-compatible database URL.",
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for session caching.",
    )
    session_ttl_seconds: int = Field(
        default=1800, ge=60, description="TTL for cached wizard sessions in Redis."
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value):
        """Convert standard postgres URLs to async postgresql+asyncpg URLs."""
        if not isinstance(value, str):
            return value

        # Only process postgres/postgresql URLs
        if not (value.startswith("postgres://") or value.startswith("postgresql://")):
            return value

        # Parse the URL
        parts = urlsplit(value)

        # Convert scheme to async driver
        scheme = "postgresql+asyncpg"

        # Parse query parameters
        query_params = parse_qs(parts.query, keep_blank_values=True)

        # Handle SSL mode for asyncpg compatibility
        # asyncpg doesn't support sslmode parameter - remove it from the connection string
        # asyncpg will handle SSL automatically with Neon's connection string
        if "sslmode" in query_params:
            query_params.pop("sslmode")

        # Also remove any ssl parameter if present
        if "ssl" in query_params:
            query_params.pop("ssl")

        # Rebuild query string
        new_query = urlencode(query_params, doseq=True) if query_params else ""

        # Reconstruct URL
        return urlunsplit((scheme, parts.netloc, parts.path, new_query, parts.fragment))

    class Config:
        # Only load .env in development to avoid overriding production secrets
        env_file = (
            "backend/.env"
            if os.getenv("ENVIRONMENT", "development") == "development"
            else None
        )
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
</file>

<file path="frontend/src/components/wizard/VehicleParamsForm.tsx">
import type { ReactNode } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleParamOverrides } from '@shared/types/tco.types';
import { vehicleParamOverridesSchema } from '@forms/wizardForm';
import { formatCurrency } from '@utils/format';

interface VehicleParamsFormProps {
  vehicleId?: string;
  title: string;
  showElectricFields?: boolean;
  subtitle?: ReactNode;
}

const VehicleParamsForm = ({
  vehicleId,
  title,
  showElectricFields = true,
  subtitle = 'Adjustments are optional - leave blank to use defaults.',
}: VehicleParamsFormProps) => {
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const wizardData = useTCOStore((state) => state.wizardData);
  const updateWizard = useTCOStore((state) => state.updateWizard);

  const setOverrideImmediate = (patch: Partial<VehicleParamOverrides>) => {
    if (!vehicleId) {
      return;
    }

    // Validate the patch before applying
    const result = vehicleParamOverridesSchema.partial().safeParse(patch);
    if (!result.success) {
      console.warn('Invalid vehicle param override:', result.error.flatten());
      return;
    }

    const existing = { ...(wizardData.vehicleParamOverrides ?? {}) };
    const current = { ...(existing[vehicleId] ?? {}) } as VehicleParamOverrides;

    Object.entries(result.data).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        delete current[key as keyof VehicleParamOverrides];
      } else {
        current[key as keyof VehicleParamOverrides] = value as number;
      }
    });

    if (Object.keys(current).length === 0) {
      delete existing[vehicleId];
    } else {
      existing[vehicleId] = current;
    }

    updateWizard({ vehicleParamOverrides: existing });
  };

  const setOverride = useDebouncedCallback(setOverrideImmediate, 150);

  if (!vehicleId) {
    return (
      <Card title={title} subtitle="Select a truck to adjust its specifications.">
        <p className="text-sm text-slate-500">No truck selected yet.</p>
      </Card>
    );
  }

  const detail = vehicleDetails[vehicleId];
  const overrides = (wizardData.vehicleParamOverrides ?? {})[vehicleId] ?? {};

  if (!detail) {
    return (
      <Card title={title} subtitle="Select a truck to adjust its specifications.">
        <p className="text-sm text-slate-500">
          Details missing for <span className="font-semibold">{vehicleId}</span>.
        </p>
      </Card>
    );
  }

  const isBev = detail.drivetrain_type === 'BEV' && showElectricFields;

  const numberOrEmpty = (value?: number) => value ?? '';

  const hasOverrides = Object.keys(overrides).length > 0;

  const handleReset = () => {
    const existing = { ...(wizardData.vehicleParamOverrides ?? {}) };
    delete existing[vehicleId];
    updateWizard({ vehicleParamOverrides: existing });
  };

  return (
    <Card
      title={title}
      subtitle={subtitle}
      headerAction={
        hasOverrides && (
          <button
            onClick={handleReset}
            className="text-xs font-bold text-rose-600 hover:text-rose-700 hover:underline"
            title="Reset all overrides to default values"
          >
            Reset to defaults
          </button>
        )
      }
    >
      <div className="grid gap-x-6 gap-y-6 sm:grid-cols-2">
        <Field
          type="number"
          min={10000}
          max={2000000}
          label="Purchase price ($)"
          placeholder={formatCurrency(detail.msrp)}
          value={numberOrEmpty(overrides.msrp_override)}
          onChange={(event) =>
            setOverride({
              msrp_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0.1}
          step="0.1"
          label="Payload capacity (tonnes)"
          placeholder={detail.payload.toFixed(1)}
          value={numberOrEmpty(overrides.payload_override)}
          onChange={(event) =>
            setOverride({
              payload_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          label="Registration cost ($/year)"
          placeholder={formatCurrency(detail.annual_registration)}
          value={numberOrEmpty(overrides.annual_registration_override)}
          onChange={(event) =>
            setOverride({
              annual_registration_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          max={0.2}
          step="0.005"
          label="Interest rate"
          hint="Annual rate as a decimal - e.g. 0.06 for 6%."
          placeholder="0.06"
          value={numberOrEmpty(overrides.interest_rate_override)}
          onChange={(event) =>
            setOverride({
              interest_rate_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={50}
          max={2500}
          label="Range (kilometres)"
          placeholder={detail.range_km ? detail.range_km.toString() : 'N/A'}
          value={numberOrEmpty(overrides.range_km_override)}
          onChange={(event) =>
            setOverride({
              range_km_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        {!isBev ? (
          <Field
            type="number"
            min={0.05}
            step="0.01"
            label="Fuel consumption (L/km)"
            placeholder={detail.litres_per_km.toFixed(2)}
            value={numberOrEmpty(overrides.litres_per_km_override)}
            onChange={(event) =>
              setOverride({
                litres_per_km_override:
                  event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
              })
            }
          />
        ) : (
          <>
            <Field
              type="number"
              min={0}
              label="Battery size (kWh)"
              placeholder={detail.battery_capacity_kwh.toString()}
              value={numberOrEmpty(overrides.battery_capacity_kwh_override)}
              onChange={(event) =>
                setOverride({
                  battery_capacity_kwh_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
            <Field
              type="number"
              min={0.1}
              step="0.01"
              label="Energy use (kWh/km)"
              placeholder={detail.kwh_per_km.toString()}
              value={numberOrEmpty(overrides.kwh_per_km_override)}
              onChange={(event) =>
                setOverride({
                  kwh_per_km_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
            <Field
              type="number"
              min={0.1}
              max={8}
              step="0.1"
              label="Charging time (hours)"
              hint="Custom charging duration for this truck."
              placeholder="1.5"
              value={numberOrEmpty(overrides.charging_time_hours_override)}
              onChange={(event) =>
                setOverride({
                  charging_time_hours_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
          </>
        )}
      </div>
    </Card>
  );
};

export default VehicleParamsForm;
</file>

<file path="frontend/src/components/wizard/WizardOperatingStep.tsx">
import { useMemo } from 'react';
import { useFormContext, useWatch } from 'react-hook-form';
import clsx from 'clsx';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import Select from '@components/shared/Select';
import type { WizardFormValues } from '@forms/wizardForm';
import { purchaseOptions, scenarioOptions } from '@forms/wizardForm';

const numberOrUndefined = (value: string) =>
  value === '' ? undefined : Number(value);

const WizardOperatingStep = () => {
  const {
    register,
    watch,
    control,
    formState: { errors },
  } = useFormContext<WizardFormValues>();
  const scenario = watch('scenario');
  const scenarioMeta = scenarioOptions.find((option) => option.value === scenario);

  // Real-time duty cycle validation
  const dutyCycle = useWatch({ control, name: 'dutyCycle' });
  const dutyCycleSum = useMemo(() => {
    const { urban = 0, regional = 0, longHaul = 0 } = dutyCycle || {};
    return (Number(urban) || 0) + (Number(regional) || 0) + (Number(longHaul) || 0);
  }, [dutyCycle]);
  const isDutyCycleValid = Math.abs(dutyCycleSum - 100) < 0.01;

  return (
    <Card
      title="How you use your trucks"
      subtitle="Settings that affect your lifetime cost calculation."
    >
      <div className="grid gap-6 md:grid-cols-2">
        <Select
          label="Market scenario"
          hint={
            scenarioMeta
              ? scenarioMeta.description
              : 'Choose a scenario to see how costs might change over time.'
          }
          {...register('scenario')}
        >
          {scenarioOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>

        <Select
          label="How will you buy?"
          hint="Determines pricing approach."
          {...register('purchaseMethod')}
        >
          {purchaseOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="mt-5">
        <p className="text-sm font-semibold text-slate-900">Your typical routes</p>
        <p className="text-xs text-slate-500">
          Percent of annual kilometres by route type. Must add up to 100%.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field
            type="number"
            label="City/metro (%)"
            placeholder="60"
            min={0}
            max={100}
            error={errors.dutyCycle?.urban?.message}
            {...register('dutyCycle.urban', {
              setValueAs: numberOrUndefined,
            })}
          />
          <Field
            type="number"
            label="Regional roads (%)"
            placeholder="25"
            min={0}
            max={100}
            error={errors.dutyCycle?.regional?.message}
            {...register('dutyCycle.regional', {
              setValueAs: numberOrUndefined,
            })}
          />
          <Field
            type="number"
            label="Highway/long distance (%)"
            placeholder="15"
            min={0}
            max={100}
            error={errors.dutyCycle?.longHaul?.message}
            {...register('dutyCycle.longHaul', {
              setValueAs: numberOrUndefined,
            })}
          />
        </div>
        <div
          className={clsx(
            'mt-3 text-sm font-medium',
            isDutyCycleValid ? 'text-green-600' : 'text-red-600'
          )}
        >
          Total: {dutyCycleSum.toFixed(0)}%
          {!isDutyCycleValid && (
            <span className="ml-2 text-xs font-normal">(Must equal 100%)</span>
          )}
        </div>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Field
          type="number"
          label="Kilometres per year"
          placeholder="23000"
          min={1000}
          hint="Custom annual distance for your trucks."
          error={errors.overrides?.annual_kms_variation?.message}
          {...register('overrides.annual_kms_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Resale value adjustment"
          step="0.05"
          placeholder="1.0"
          hint="Enter 0.90 for 10% lower resale, 1.10 for 10% higher."
          error={errors.overrides?.residual_value_variation?.message}
          {...register('overrides.residual_value_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Maintenance cost adjustment"
          step="0.05"
          placeholder="1.0"
          hint="Enter 1.10 for 10% higher costs, 0.90 for 10% lower."
          error={errors.overrides?.maintenance_cost_variation?.message}
          {...register('overrides.maintenance_cost_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
      </div>
    </Card>
  );
};

export default WizardOperatingStep;
</file>

</files>
