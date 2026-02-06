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
        expect(result.breakdown.upfront_costs.purchase_cost).toBeGreaterThan(0);
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
