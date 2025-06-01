"""
Financial utility functions for TCO analysis.
Handles present value calculations and discounting.
"""

import data.constants as const


def calculate_present_value(annual_amount: float, years: int, discount_rate: float = const.DISCOUNT_RATE) -> float:
    """
    Calculate present value of an annual amount over a number of years.
    
    Formula: PV = Annual × [(1 - (1 + r)^-n) / r]
    where r = discount rate, n = number of years
    """
    if discount_rate == 0:
        return annual_amount * years
    
    return annual_amount * ((1 - (1 + discount_rate) ** -years) / discount_rate)


def discount_to_present(amount: float, year: int, discount_rate: float = const.DISCOUNT_RATE) -> float:
    """
    Discount a future amount to present value.
    
    Formula: PV = Future Value / (1 + r)^(year - 1)
    where r = discount rate
    """
    return amount / (1 + discount_rate) ** (year - 1)


def calculate_npv_of_payments(monthly_payment: float, num_payments: int, discount_rate: float = const.DISCOUNT_RATE) -> float:
    """
    Calculate net present value of a series of monthly payments.
    
    Args:
        monthly_payment: Monthly payment amount
        num_payments: Total number of payments
        discount_rate: Annual discount rate
    
    Returns:
        Net present value of all payments
    """
    npv = 0.0
    
    for month in range(1, num_payments + 1):
        # Calculate the discount factor for this month
        year_fraction = month / 12.0
        discount_factor = (1 + discount_rate) ** year_fraction
        npv += monthly_payment / discount_factor
    
    return npv


def calculate_annualised_cost(total_cost: float, years: int, discount_rate: float = const.DISCOUNT_RATE) -> float:
    """
    Convert a total cost to an equivalent annual cost.
    
    This is the inverse of present value calculation.
    """
    if discount_rate == 0:
        return total_cost / years
    
    return total_cost / ((1 - (1 + discount_rate) ** -years) / discount_rate)


def escalate_cost(base_cost: float, escalation_rate: float, year: int) -> float:
    """
    Escalate a cost by a given rate over a number of years.
    
    Formula: Future Cost = Base Cost × (1 + rate)^year
    """
    return base_cost * (1 + escalation_rate) ** year 