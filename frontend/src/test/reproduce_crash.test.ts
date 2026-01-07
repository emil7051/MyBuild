import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload, DutyCycle } from '@shared/types/tco.types';

describe('TCO Calculator Crash Reproduction', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('should handle zero-sum duty cycle without crashing', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 0, regional: 0, longHaul: 0 },
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
    expect(result.cost_per_km).not.toBeNaN();
  });

  it('should handle NaN duty cycle values without crashing', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: NaN, regional: 0, longHaul: 0 } as unknown as DutyCycle,
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
  });

  it('should handle partial duty cycle objects', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 50 } as unknown as DutyCycle,
    };

    // Should not throw
    const result = calculateTco(payload);

    // Expect valid numbers, not NaN
    expect(result.total_cost).not.toBeNaN();
  });
});
