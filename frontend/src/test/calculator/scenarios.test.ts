import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Economic Scenarios', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Baseline Scenario', () => {
    it('should produce valid results', () => {
      const result = calculateTco(basePayload);
      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.annual_cost).toBeGreaterThan(0);
      expect(result.cost_per_km).toBeGreaterThan(0);
    });
  });

  describe('Technology Breakthrough Scenario', () => {
    it('should produce lower BEV costs than baseline', () => {
      const baseline = calculateTco(basePayload);
      const breakthrough = calculateTco({
        ...basePayload,
        scenario_name: 'technology_breakthrough',
      });

      // Technology breakthrough should reduce BEV costs
      expect(breakthrough.total_cost).toBeLessThan(baseline.total_cost);
    });

    it('should have lower battery costs due to price trajectory', () => {
      const baseline = calculateTco(basePayload);
      const breakthrough = calculateTco({
        ...basePayload,
        scenario_name: 'technology_breakthrough',
      });

      expect(breakthrough.breakdown.battery_replacement_cost).toBeLessThanOrEqual(
        baseline.breakdown.battery_replacement_cost
      );
    });
  });

  describe('Oil Crisis Scenario', () => {
    it('should produce higher diesel costs than baseline', () => {
      const dieselBaseline = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'baseline',
      });
      const dieselCrisis = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'oil_crisis',
      });

      expect(dieselCrisis.breakdown.fuel_cost).toBeGreaterThan(
        dieselBaseline.breakdown.fuel_cost
      );
    });

    it('should make BEV more competitive vs diesel', () => {
      const bevCrisis = calculateTco({
        ...basePayload,
        scenario_name: 'oil_crisis',
      });
      const dieselCrisis = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        scenario_name: 'oil_crisis',
      });

      // In oil crisis, BEV advantage should be greater
      const bevAdvantage = dieselCrisis.total_cost - bevCrisis.total_cost;
      expect(bevAdvantage).toBeGreaterThan(0);
    });
  });

  describe('Scenario Comparison', () => {
    it('should produce distinct results for each scenario', () => {
      const scenarios = ['baseline', 'technology_breakthrough', 'oil_crisis'] as const;
      const results = scenarios.map((scenario) =>
        calculateTco({ ...basePayload, scenario_name: scenario }).total_cost
      );

      // All three should be different
      expect(new Set(results).size).toBe(3);
    });
  });
});
