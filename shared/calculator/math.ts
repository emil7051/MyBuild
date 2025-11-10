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
