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
