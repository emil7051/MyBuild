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
      expect(result.breakdown.nominal_costs.financing_cost).toBe(0);
    });

    it('should have full purchase cost upfront', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'outright',
      });
      expect(result.breakdown.upfront_costs.purchase_cost).toBeGreaterThan(0);
    });
  });

  describe('Financed Purchase', () => {
    it('should have non-zero financing cost', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
      });
      expect(result.breakdown.nominal_costs.financing_cost).toBeGreaterThan(0);
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
      expect(financed.breakdown.upfront_costs.purchase_cost).toBeLessThan(
        outright.breakdown.upfront_costs.purchase_cost
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

      expect(higherRate.breakdown.nominal_costs.financing_cost).toBeGreaterThan(
        standardRate.breakdown.nominal_costs.financing_cost
      );
    });

    it('should have zero financing cost with 0% rate', () => {
      const result = calculateTco({
        ...basePayload,
        purchase_method: 'financed',
        vehicle_overrides: { interest_rate_override: 0 },
      });

      expect(result.breakdown.nominal_costs.financing_cost).toBe(0);
    });
  });
});
