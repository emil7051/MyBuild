"""
Financial calculations for vehicle TCO analysis.
Handles purchase costs, financing, and depreciation.
"""

import numpy_financial as npf
from typing import Optional

import data.constants as const
from data import policies
from data.scenarios import EconomicScenario
from data.vehicles import VehicleModel


def calculate_stamp_duty(msrp: float, is_bev: bool = False) -> float:
    """Calculate stamp duty for a vehicle considering policy exemptions."""
    base_stamp_duty = msrp * const.STAMP_DUTY_RATE
    return policies.calculate_stamp_duty_with_exemption(base_stamp_duty, is_bev)


def calculate_rebate(msrp: float, drivetrain_type: str) -> float:
    """Calculate applicable rebates for vehicle purchase."""
    if drivetrain_type == 'BEV':
        return policies.calculate_bev_purchase_rebate(msrp)
    return 0.0


def calculate_initial_cost(msrp: float, drivetrain_type: str) -> float:
    """
    Calculate total initial cost including stamp duty and rebates.
    
    Initial cost = MSRP + stamp duty - rebates
    """
    is_bev = drivetrain_type == 'BEV'
    stamp_duty = calculate_stamp_duty(msrp, is_bev)
    rebate = calculate_rebate(msrp, drivetrain_type)
    
    return msrp + stamp_duty - rebate


class FinancingCalculator:
    """Handles all financing-related calculations."""
    
    @staticmethod
    def calculate_down_payment(initial_cost: float) -> float:
        """Calculate down payment amount."""
        return initial_cost * const.DOWN_PAYMENT_RATE
    
    @staticmethod
    def calculate_loan_amount(initial_cost: float, down_payment: float) -> float:
        """Calculate loan amount after down payment."""
        return initial_cost - down_payment
    
    @staticmethod
    def calculate_interest_rate(drivetrain_type: str) -> float:
        """Calculate financing interest rate considering policy subsidies."""
        is_bev = drivetrain_type == 'BEV'
        return policies.calculate_financing_interest_rate(const.INTEREST_RATE, is_bev)
    
    @staticmethod
    def calculate_monthly_payment(loan_amount: float, interest_rate: float) -> float:
        """Calculate monthly loan payment."""
        monthly_rate = interest_rate / 12
        num_payments = const.FINANCING_TERM * 12
        return float(npf.pmt(monthly_rate, num_payments, -loan_amount))
    
    @staticmethod
    def calculate_total_financing_cost(monthly_payment: float, loan_amount: float) -> float:
        """Calculate total financing cost over the term."""
        num_payments = const.FINANCING_TERM * 12
        total_payments = monthly_payment * num_payments
        return total_payments - loan_amount


class DepreciationCalculator:
    """Handles vehicle depreciation calculations."""
    
    def __init__(self, initial_cost: float, scenario: Optional[EconomicScenario] = None):
        self.initial_cost = initial_cost
        self.scenario = scenario
        self.first_year_depreciation = initial_cost * const.DEPRECIATION_RATE_FIRST_YEAR
        self.annual_depreciation_rate = const.DEPRECIATION_RATE_ONGOING
    
    def get_depreciation_year(self, year: int, drivetrain_type: str = 'Diesel') -> float:
        """Get depreciation for a specific year."""
        if year == 1:
            return self.first_year_depreciation
        
        # Calculate remaining value and apply ongoing rate
        remaining_value = self.initial_cost - self.first_year_depreciation
        for y in range(2, year):
            remaining_value *= (1 - self.annual_depreciation_rate)
        
        # Apply BEV residual value multiplier from scenario if applicable
        if (drivetrain_type == 'BEV' and 
            self.scenario and 
            self.scenario.bev_residual_value_multiplier and
            year <= len(self.scenario.bev_residual_value_multiplier)):
            remaining_value *= self.scenario.bev_residual_value_multiplier[year - 1]
        
        return remaining_value * self.annual_depreciation_rate
    
    def get_total_depreciation(self, drivetrain_type: str = 'Diesel') -> float:
        """Calculate total depreciation over vehicle life."""
        total = 0.0
        for year in range(1, const.VEHICLE_LIFE + 1):
            total += self.get_depreciation_year(year, drivetrain_type)
        return total

    def get_residual_value(self, year: int, drivetrain_type: str = 'Diesel') -> float:
        """
        Calculate residual value at the end of a specific year.
        
        Residual value = Initial cost - Total depreciation up to that year
        """
        if year == 0:
            return self.initial_cost
            
        # Start with initial cost and apply depreciation year by year
        residual_value = self.initial_cost - self.first_year_depreciation
        
        # Apply ongoing depreciation for years 2 through the specified year
        for y in range(2, year + 1):
            residual_value *= (1 - self.annual_depreciation_rate)
        
        # Apply BEV residual value multiplier from scenario if applicable
        if (drivetrain_type == 'BEV' and 
            self.scenario and 
            self.scenario.bev_residual_value_multiplier and
            year <= len(self.scenario.bev_residual_value_multiplier)):
            residual_value *= self.scenario.bev_residual_value_multiplier[year - 1]
        
        return residual_value 