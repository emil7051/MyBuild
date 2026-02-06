import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { OVERRIDE_LIMITS } from '@shared/data/constants';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Override sanitization', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('should clamp fuel price variation to the supported range', () => {
    const maxFuelVariation = OVERRIDE_LIMITS.cost.fuel_price_variation.max;
    const clamped = calculateTco({
      ...basePayload,
      vehicle_id: 'DSL001',
      overrides: { fuel_price_variation: maxFuelVariation * 5 },
    });

    const maxed = calculateTco({
      ...basePayload,
      vehicle_id: 'DSL001',
      overrides: { fuel_price_variation: maxFuelVariation },
    });

    expect(clamped.breakdown.npv_costs.fuel_cost).toBeCloseTo(maxed.breakdown.npv_costs.fuel_cost, 5);
  });

  it('should ignore annual kms overrides below the minimum', () => {
    const minAnnualKms = OVERRIDE_LIMITS.cost.annual_kms_variation.min;
    const base = calculateTco(basePayload);
    const underMin = calculateTco({
      ...basePayload,
      overrides: { annual_kms_variation: minAnnualKms - 1 },
    });

    expect(underMin.cost_per_km).toBeCloseTo(base.cost_per_km, 6);
  });

  it('should keep charging labour costs finite for invalid BEV overrides', () => {
    const result = calculateTco({
      ...basePayload,
      vehicle_id: 'BEV007',
      vehicle_overrides: { range_km_override: 0, charging_time_hours_override: 0 },
    });

    expect(Number.isFinite(result.breakdown.npv_costs.charging_labour_cost)).toBe(true);
    expect(result.breakdown.npv_costs.charging_labour_cost).not.toBeNaN();
  });
});
