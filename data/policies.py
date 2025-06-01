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
        return 0 <= self.percentage <= 1 and (self.max_amount is None or self.max_amount > 0)


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
        return 0 <= self.grant_percentage <= 1 and (self.max_amount is None or self.max_amount > 0)

# ============================================================================
# POLICY DEFINITIONS
# ============================================================================

# Define all available policies
POLICIES = {
    'purchase_rebate': PurchaseRebate(
        name='Fixed Purchase Rebate',
        description='Fixed dollar amount rebate for new BEV purchases',
        enabled=False,
        amount=0
    ),
    
    'percentage_rebate': PercentageRebate(
        name='Percentage Purchase Rebate',
        description='Percentage-based rebate on BEV purchase price',
        enabled=False,
        percentage=0.0,
        max_amount=None
    ),
    
    'stamp_duty_exemption': StampDutyExemption(
        name='Stamp Duty Exemption',
        description='Full or partial exemption from stamp duty for BEVs',
        enabled=False,
        exemption_percentage=0.0
    ),

    'carbon_price': CarbonPrice(
        name='Carbon Pricing',
        description='Price on carbon emissions from diesel vehicles',
        enabled=False,
        price_per_tonne=0
    ),
    
    'green_loan_subsidy': GreenLoanSubsidy(
        name='Green Loan Subsidy',
        description='Reduced interest rate for BEV financing',
        enabled=False,
        rate_reduction=0.0
    ),
    
    'charging_grant': ChargingInfrastructureGrant(
        name='Charging Infrastructure Grant',
        description='Grant for charging infrastructure installation',
        enabled=False,
        grant_percentage=0.0,
        max_amount=None
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
    if POLICIES['purchase_rebate'].enabled:
        bev_purchase_rebate += POLICIES['purchase_rebate'].amount
    
    # Percentage rebate
    if POLICIES['percentage_rebate'].enabled:
        percentage_rebate = vehicle_price * POLICIES['percentage_rebate'].percentage
        if POLICIES['percentage_rebate'].max_amount:
            percentage_rebate = min(percentage_rebate, POLICIES['percentage_rebate'].max_amount)
        bev_purchase_rebate += percentage_rebate
    
    return bev_purchase_rebate


def calculate_stamp_duty_with_exemption(base_stamp_duty: float, is_bev: bool) -> float:
    """Calculate stamp duty considering BEV exemptions."""
    if is_bev and POLICIES['stamp_duty_exemption'].enabled:
        exemption = base_stamp_duty * POLICIES['stamp_duty_exemption'].exemption_percentage
        return base_stamp_duty - exemption
    return base_stamp_duty


def calculate_financing_interest_rate(base_rate: float, is_bev: bool) -> float:
    """Calculate financing interest rate considering BEV subsidies."""
    if is_bev and POLICIES['green_loan_subsidy'].enabled:
        return max(0, base_rate - POLICIES['green_loan_subsidy'].rate_reduction)
    return base_rate


def calculate_annual_policy_charges(is_bev: bool, annual_emissions_tonnes: float = 0) -> float:
    """Calculate annual charges/credits based on active policies."""
    annual_charges = 0.0
    

    # Carbon pricing (diesel only)
    if not is_bev and POLICIES['carbon_price'].enabled:
        annual_charges += annual_emissions_tonnes * POLICIES['carbon_price'].price_per_tonne
    
    return annual_charges


def calculate_infrastructure_grant(infrastructure_cost: float) -> float:
    """Calculate charging infrastructure grant amount."""
    if POLICIES['charging_grant'].enabled:
        grant = infrastructure_cost * POLICIES['charging_grant'].grant_percentage
        if POLICIES['charging_grant'].max_amount:
            grant = min(grant, POLICIES['charging_grant'].max_amount)
        return grant
    return 0.0


# ============================================================================
# POLICY SCENARIOS
# ============================================================================ 

# Example policy scenarios
def enable_standard_incentives():
    """Enable a standard set of BEV incentives."""
    POLICIES['purchase_rebate'].enabled = True
    POLICIES['purchase_rebate'].amount = 20000
    
    POLICIES['stamp_duty_exemption'].enabled = True
    POLICIES['stamp_duty_exemption'].exemption_percentage = 1.0
    
    POLICIES['green_loan_subsidy'].enabled = True
    POLICIES['green_loan_subsidy'].rate_reduction = 0.02


def enable_aggressive_incentives():
    """Enable aggressive BEV incentives plus diesel disincentives."""
    
    # BEV incentives
    POLICIES['percentage_rebate'].enabled = True
    POLICIES['percentage_rebate'].percentage = 0.15
    POLICIES['percentage_rebate'].max_amount = 50000
    
    POLICIES['stamp_duty_exemption'].enabled = True
    POLICIES['stamp_duty_exemption'].exemption_percentage = 1.0
    
    POLICIES['green_loan_subsidy'].enabled = True
    POLICIES['green_loan_subsidy'].rate_reduction = 0.03
    
    POLICIES['charging_grant'].enabled = True
    POLICIES['charging_grant'].grant_percentage = 0.5
    POLICIES['charging_grant'].max_amount = 500000
    
    # Diesel disincentives
    POLICIES['carbon_price'].enabled = True
    POLICIES['carbon_price'].price_per_tonne = 50


def disable_all_policies():
    """Disable all policy incentives."""
    for policy in POLICIES.values():
        policy.enabled = False 