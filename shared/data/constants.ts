/**
 * @file TCO Calculator Constants
 * @module shared/data/constants
 *
 * Central configuration for all calculation parameters.
 * Values are sourced from industry research and Australian government data.
 *
 * This file re-exports from:
 * - constants.generated.ts (auto-generated from Python data - DO NOT EDIT)
 * - constants.future.ts (manually maintained planned features)
 *
 * To update constants:
 * 1. Edit data/constants.py (Python source of truth)
 * 2. Run: python scripts/generate_vehicle_catalog_ts.py
 * 3. The generated constants will be updated in constants.generated.ts
 */

// Re-export auto-generated constants (from Python data/constants.py)
import { CONSTANTS } from './constants.generated';
export { CONSTANTS };
export type { ConstantCatalog, ConstantsSchema } from './constants.generated';

export const DUTY_CYCLE_TOTAL_TOLERANCE =
  typeof CONSTANTS.DUTY_CYCLE_TOTAL_TOLERANCE === 'number'
    ? CONSTANTS.DUTY_CYCLE_TOTAL_TOLERANCE
    : 0.5;

export type OverrideLimit = {
  min: number;
  max: number;
};

export type OverrideLimits = {
  cost: Record<string, OverrideLimit>;
  vehicle: Record<string, OverrideLimit>;
};

export const OVERRIDE_LIMITS = CONSTANTS.OVERRIDE_LIMITS as OverrideLimits;

// Re-export manually maintained future constants
export { FUTURE_CONSTANTS } from './constants.future';
