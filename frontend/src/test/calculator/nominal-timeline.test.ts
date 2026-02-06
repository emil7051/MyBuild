import { describe, expect, it } from 'vitest';
import { calculateNominalCostTimeline } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('calculateNominalCostTimeline', () => {
  const basePayload: Omit<CalculationRequestPayload, 'vehicle_id'> = {
    scenario_name: 'baseline',
    purchase_method: 'financed',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('returns a year 0 upfront point plus a full 15-year timeline', () => {
    const timeline = calculateNominalCostTimeline({
      ...basePayload,
      vehicle_id: 'BEV001',
    });

    expect(timeline).toHaveLength(16);
    expect(timeline[0].year).toBe(0);
    expect(timeline[timeline.length - 1].year).toBe(15);
  });

  it('captures financing front-loading, battery replacement, and residual credit timing', () => {
    const timeline = calculateNominalCostTimeline({
      ...basePayload,
      vehicle_id: 'BEV001',
    });

    expect(timeline[1].annualCost).toBeGreaterThan(timeline[6].annualCost);
    expect(timeline[8].annualCost).toBeGreaterThan(timeline[7].annualCost);
    expect(timeline[15].annualCost).toBeLessThan(0);
  });
});
