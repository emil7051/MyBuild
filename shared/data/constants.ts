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
export { CONSTANTS } from './constants.generated';
export type { ConstantCatalog } from '../types/tco.types';

// Re-export manually maintained future constants
export { FUTURE_CONSTANTS } from './constants.future';
