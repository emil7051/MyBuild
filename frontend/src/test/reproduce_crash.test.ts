import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload, DutyCycle } from '@shared/types/tco.types';

describe('TCO Calculator Duty-Cycle Validation', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('rejects zero-sum duty cycle', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 0, regional: 0, longHaul: 0 },
    };

    expect(() => calculateTco(payload)).toThrow('Duty cycle splits must sum to ~100%.');
  });

  it('rejects NaN duty cycle values', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: NaN, regional: 0, longHaul: 0 } as unknown as DutyCycle,
    };

    expect(() => calculateTco(payload)).toThrow(
      'Duty cycle values must be finite numbers between 0 and 100.'
    );
  });

  it('rejects partial duty cycle objects', () => {
    const payload = {
      ...basePayload,
      duty_cycle: { urban: 50 } as unknown as DutyCycle,
    };

    expect(() => calculateTco(payload)).toThrow(
      'Duty cycle values must be finite numbers between 0 and 100.'
    );
  });
});
