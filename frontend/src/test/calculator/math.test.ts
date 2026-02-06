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
      expect(pv).toBeCloseTo(8107.82, 0); // Annuity-due PV
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
      expect(pv).toBeCloseTo(1000, 0);
    });
  });

  describe('discountToPresent', () => {
    it('should not discount year 1 (annuity-due convention)', () => {
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
      expect(annual).toBeCloseTo(1233.38, 0);
    });

    it('should handle zero NPV', () => {
      expect(calculateAnnualisedCost(0, 10, 0.05)).toBe(0);
    });

    it('should invert calculatePresentValue under annuity-due convention', () => {
      const annualAmount = 1000;
      const pv = calculatePresentValue(annualAmount, 10, 0.05);
      const annualised = calculateAnnualisedCost(pv, 10, 0.05);
      expect(annualised).toBeCloseTo(annualAmount, 6);
    });
  });
});
