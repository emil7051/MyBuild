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
