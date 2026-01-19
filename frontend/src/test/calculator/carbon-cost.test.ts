import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Carbon cost calculations', () => {
  it('should apply diesel efficiency improvements to carbon cost', () => {
    const baselineScenario = SCENARIO_DEFINITIONS.baseline;
    const originalCarbon = [...baselineScenario.carbon_price_trajectory];
    const originalEfficiency = [...baselineScenario.diesel_efficiency_improvement];

    try {
      baselineScenario.carbon_price_trajectory = originalCarbon.map(() => 100);
      baselineScenario.diesel_efficiency_improvement = originalEfficiency.map(() => 1);

      const payload: CalculationRequestPayload = {
        vehicle_id: 'DSL001',
        scenario_name: 'baseline',
        purchase_method: 'outright',
        duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
      };

      const noImprovement = calculateTco(payload);

      baselineScenario.diesel_efficiency_improvement = originalEfficiency.map(() => 0.8);
      const withImprovement = calculateTco(payload);

      expect(withImprovement.breakdown.carbon_cost).toBeGreaterThan(0);
      expect(withImprovement.breakdown.carbon_cost).toBeLessThan(
        noImprovement.breakdown.carbon_cost
      );
    } finally {
      baselineScenario.carbon_price_trajectory = originalCarbon;
      baselineScenario.diesel_efficiency_improvement = originalEfficiency;
    }
  });
});
