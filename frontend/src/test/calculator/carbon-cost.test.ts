import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

const cloneJson = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

describe('Carbon cost calculations', () => {
  it('should apply diesel efficiency improvements to carbon cost', () => {
    const scenarios = SCENARIO_DEFINITIONS as Record<
      string,
      (typeof SCENARIO_DEFINITIONS)['baseline']
    >;
    const originalBaseline = scenarios.baseline;
    const baselineScenario = cloneJson(originalBaseline);
    scenarios.baseline = baselineScenario;

    try {
      baselineScenario.carbon_price_trajectory = baselineScenario.carbon_price_trajectory.map(() => 100);
      baselineScenario.diesel_efficiency_improvement = baselineScenario.diesel_efficiency_improvement.map(
        () => 1
      );

      const payload: CalculationRequestPayload = {
        vehicle_id: 'DSL001',
        scenario_name: 'baseline',
        purchase_method: 'outright',
        duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
      };

      const noImprovement = calculateTco(payload);

      baselineScenario.diesel_efficiency_improvement = baselineScenario.diesel_efficiency_improvement.map(
        () => 0.8
      );
      const withImprovement = calculateTco(payload);

      expect(withImprovement.breakdown.npv_costs.carbon_cost).toBeGreaterThan(0);
      expect(withImprovement.breakdown.npv_costs.carbon_cost).toBeLessThan(
        noImprovement.breakdown.npv_costs.carbon_cost
      );
    } finally {
      scenarios.baseline = originalBaseline;
    }
  });
});
