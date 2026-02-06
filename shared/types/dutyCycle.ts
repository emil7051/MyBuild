import { DUTY_CYCLE_TOTAL_TOLERANCE } from '../data/constants';
import type { DutyCycle } from './tco.types';

export const DEFAULT_DUTY_CYCLE: DutyCycle = {
  urban: 60,
  regional: 25,
  longHaul: 15,
};

export type DutyCycleValidationResult = {
  valid: boolean;
  reason?: 'invalid_value' | 'invalid_total';
  total: number;
};

const isFinitePercentage = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100;

export const validateDutyCycle = (dutyCycle: DutyCycle): DutyCycleValidationResult => {
  const values = [dutyCycle.urban, dutyCycle.regional, dutyCycle.longHaul];
  if (!values.every(isFinitePercentage)) {
    return {
      valid: false,
      reason: 'invalid_value',
      total: Number.NaN,
    };
  }

  const total = dutyCycle.urban + dutyCycle.regional + dutyCycle.longHaul;
  if (Math.abs(total - 100) > DUTY_CYCLE_TOTAL_TOLERANCE) {
    return {
      valid: false,
      reason: 'invalid_total',
      total,
    };
  }

  return {
    valid: true,
    total,
  };
};

export const getDutyCycleErrorMessage = (result: DutyCycleValidationResult): string => {
  if (result.reason === 'invalid_total') {
    return 'Duty cycle splits must sum to ~100%.';
  }
  return 'Duty cycle values must be finite numbers between 0 and 100.';
};

