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

  // TEST-002: Verify PV convention consistency (CALC-003)
  describe('PV Convention Consistency (CALC-003)', () => {
    it('calculateNpvOfAnnualCashflows should not discount year 1', () => {
      // A single cashflow in year 1 should equal its face value
      const npv = calculateNpvOfAnnualCashflows([1000], 0.05);
      expect(npv).toBe(1000);
    });

    it('calculateNpvOfAnnualCashflows should discount year 2 by one period', () => {
      // A single cashflow in year 2 should be discounted once
      const npv = calculateNpvOfAnnualCashflows([0, 1000], 0.05);
      expect(npv).toBeCloseTo(952.38, 0);
    });

    it('constant annual cashflows via calculateNpvOfAnnualCashflows should match expected NPV', () => {
      // 10 years of $1000/year with year 1 not discounted (annuity due style)
      const cashflows = Array(10).fill(1000);
      const npv = calculateNpvOfAnnualCashflows(cashflows, 0.05);
      
      // This should be higher than ordinary annuity PV because year 1 is not discounted
      const ordinaryAnnuityPv = calculatePresentValue(1000, 10, 0.05);
      expect(npv).toBeGreaterThan(ordinaryAnnuityPv);
    });

    it('discountToPresent convention should match calculateNpvOfAnnualCashflows', () => {
      // Verify that discountToPresent(amount, year) matches array-based NPV
      const amount = 1000;
      for (let year = 1; year <= 5; year++) {
        const singleCashflow = Array(year).fill(0);
        singleCashflow[year - 1] = amount;
        const npvFromArray = calculateNpvOfAnnualCashflows(singleCashflow, 0.05);
        const npvFromDiscount = discountToPresent(amount, year, 0.05);
        expect(npvFromArray).toBeCloseTo(npvFromDiscount, 10);
      }
    });
  });
});
