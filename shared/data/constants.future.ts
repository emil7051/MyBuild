/**
 * @file Future/Planned Constants
 * @module shared/data/constants.future
 *
 * MANUALLY MAINTAINED - Not auto-generated
 *
 * These constants are reserved for planned features that are not yet
 * implemented in the calculator. Moving here instead of deleting preserves
 * them for future implementation.
 *
 * When a feature is implemented, move its constants to data/constants.py
 * and regenerate the TypeScript constants.
 */

export const FUTURE_CONSTANTS = {
  /** Annual battery capacity degradation rate (2.5% per year) */
  BATTERY_DEGRADATION_RATE: 0.025,

  /** Cost of DC fast charger installation */
  CHARGER_COST: 300000,

  /** Australian fuel tax credit rate per litre */
  FUEL_TAX_CREDIT: 0.203,

  /** Road user charge per km (heavy vehicles) */
  ROAD_USER_CHARGE: 0.305,

  /** Annual inflation rate for cost projections */
  INFLATION_RATE: 0.025,

  /** Expected lifespan of charging infrastructure */
  INFRASTRUCTURE_LIFE: 15,

  /** Solar PV and battery storage installation costs */
  SOLAR_MAINTENANCE: 0.15,
  SOLAR_PANEL_INSTALLATION: 1285,
  STORAGE_INSTALLATION: 423,
  STORAGE_MAINTENANCE: 0.025,

  /** Grid upgrade costs for charging infrastructure */
  GRID_UPGRADE: 1000000,
} as const;
