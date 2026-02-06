/**
 * @file TCO Calculator - Core Calculation Engine
 * @module shared/calculator/tcoCalculator
 *
 * This module contains the main TCO (Total Cost of Ownership) calculation
 * logic for comparing BEV and Diesel vehicles over a 15-year lifecycle.
 *
 * Key functions:
 * - calculateTco(): Calculate TCO for a single vehicle
 * - calculateComparison(): Calculate TCO for multiple vehicles
 *
 * Cost components calculated:
 * - Purchase cost (including stamp duty, rebates)
 * - Fuel/energy costs (with scenario trajectories)
 * - Maintenance costs
 * - Insurance and registration
 * - Battery replacement (BEV only, year 8)
 * - Carbon costs (if scenario includes carbon pricing)
 * - Charging labor costs (BEV only)
 * - Payload penalty (lost revenue from reduced capacity)
 * - Residual value (end-of-life)
 *
 * @see shared/calculator/math.ts for financial utilities
 * @see shared/data/constants.ts for configuration values
 * @see shared/types/tco.types.ts for type definitions
 */

import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
  CostBreakdown,
  CostOverrides,
  EconomicScenarioDefinition,
  DutyCycle,
  PurchaseMethod,
  ScenarioKey,
  VehicleDetail,
  VehicleParamOverrides,
} from '../types/tco.types';
import { VEHICLE_BY_ID, VEHICLE_CATALOG_VERSION, VEHICLE_DETAILS } from '../data/vehicleCatalog';
import { CONSTANTS } from '../data/constants';
import { SCENARIO_DEFINITIONS } from '../data/scenarios';
import { POLICY_CONFIG } from '../data/policies';
import {
  calculateAnnualisedCost,
  calculateNpvOfAnnualCashflows,
  calculateNpvOfPayments,
  calculatePresentValue,
  discountToPresent,
} from './math';

type WeightClass = VehicleDetail['weight_class'];
type ChargingMix = Record<'retail' | 'offpeak' | 'public' | 'solar', number>;

/**
 * Validates that a value is a Record with expected keys.
 * Throws descriptive error if validation fails.
 */
const assertRecord = <K extends string, V>(
  value: unknown,
  name: string,
  expectedKeys?: K[]
): Record<K, V> => {
  if (!value || typeof value !== 'object') {
    throw new Error(`${name} must be an object, got ${typeof value}`);
  }
  if (expectedKeys) {
    for (const key of expectedKeys) {
      if (!(key in value)) {
        throw new Error(`${name} is missing required key: ${key}`);
      }
    }
  }
  return value as Record<K, V>;
};

/**
 * Validates nested Record structure for maintenance costs.
 */
const assertMaintenanceCosts = (
  value: unknown
): Record<'BEV' | 'Diesel', Record<WeightClass, number>> => {
  const record = assertRecord<'BEV' | 'Diesel', unknown>(
    value,
    'MAINTENANCE_COST_PER_KM',
    ['BEV', 'Diesel']
  );
  assertRecord<WeightClass, number>(record.BEV, 'MAINTENANCE_COST_PER_KM.BEV');
  assertRecord<WeightClass, number>(record.Diesel, 'MAINTENANCE_COST_PER_KM.Diesel');
  return record as Record<'BEV' | 'Diesel', Record<WeightClass, number>>;
};

const DEFAULT_DUTY_CYCLE: DutyCycle = { urban: 60, regional: 25, longHaul: 15 };

const clampNumber = (value: number, min: number, max: number): number =>
  Math.min(Math.max(value, min), max);

const toFiniteNumber = (value: unknown): number | undefined => {
  if (typeof value !== 'number' || Number.isNaN(value) || !Number.isFinite(value)) {
    return undefined;
  }
  return value;
};

const toBoolean = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') {
    return value;
  }
  return undefined;
};

const clampOverrideValue = (value: unknown, min: number, max: number): number | undefined => {
  const numeric = toFiniteNumber(value);
  if (numeric === undefined) {
    return undefined;
  }
  return clampNumber(numeric, min, max);
};

const clampOverrideAboveMin = (value: unknown, min: number, max: number): number | undefined => {
  const numeric = toFiniteNumber(value);
  if (numeric === undefined || numeric < min) {
    return undefined;
  }
  return Math.min(numeric, max);
};

/**
 * Sanitizes calculation payload to prevent NaN and invalid values from reaching calculations.
 * This is a defensive layer - frontend validation should catch most issues.
 */
const sanitizePayload = (payload: CalculationRequestPayload): CalculationRequestPayload => {
  const sanitized = { ...payload };

  // Sanitize duty cycle - ensure all values are valid positive numbers
  if (sanitized.duty_cycle) {
    sanitized.duty_cycle = {
      urban: Math.max(0, Number(sanitized.duty_cycle.urban) || 0),
      regional: Math.max(0, Number(sanitized.duty_cycle.regional) || 0),
      longHaul: Math.max(0, Number(sanitized.duty_cycle.longHaul) || 0),
    };
  }

  // Sanitize cost overrides - ensure they're positive numbers or undefined
  if (sanitized.overrides) {
    const cleanOverrides: CostOverrides = {};
    const annualKmsVariation = clampOverrideAboveMin(
      sanitized.overrides.annual_kms_variation,
      5000,
      250000
    );
    if (annualKmsVariation !== undefined) {
      cleanOverrides.annual_kms_variation = annualKmsVariation;
    }
    const residualValueVariation = clampOverrideValue(
      sanitized.overrides.residual_value_variation,
      0.5,
      1.5
    );
    if (residualValueVariation !== undefined) {
      cleanOverrides.residual_value_variation = residualValueVariation;
    }
    const fuelPriceVariation = clampOverrideValue(
      sanitized.overrides.fuel_price_variation,
      0.5,
      2.0
    );
    if (fuelPriceVariation !== undefined) {
      cleanOverrides.fuel_price_variation = fuelPriceVariation;
    }
    const electricityPriceVariation = clampOverrideValue(
      sanitized.overrides.electricity_price_variation,
      0.5,
      2.0
    );
    if (electricityPriceVariation !== undefined) {
      cleanOverrides.electricity_price_variation = electricityPriceVariation;
    }
    const maintenanceCostVariation = clampOverrideValue(
      sanitized.overrides.maintenance_cost_variation,
      0.5,
      1.5
    );
    if (maintenanceCostVariation !== undefined) {
      cleanOverrides.maintenance_cost_variation = maintenanceCostVariation;
    }
    const batteryLifeVariation = clampOverrideValue(
      sanitized.overrides.battery_life_variation,
      0.5,
      1.5
    );
    if (batteryLifeVariation !== undefined) {
      cleanOverrides.battery_life_variation = batteryLifeVariation;
    }
    const chargingEfficiencyVariation = clampOverrideValue(
      sanitized.overrides.charging_efficiency_variation,
      0.7,
      1.3
    );
    if (chargingEfficiencyVariation !== undefined) {
      cleanOverrides.charging_efficiency_variation = chargingEfficiencyVariation;
    }
    const applyRoadUserChargeBev = toBoolean(sanitized.overrides.apply_road_user_charge_bev);
    if (applyRoadUserChargeBev !== undefined) {
      cleanOverrides.apply_road_user_charge_bev = applyRoadUserChargeBev;
    }
    sanitized.overrides = cleanOverrides;
  }

  // Sanitize vehicle param overrides - ensure they're positive numbers or undefined
  if (sanitized.vehicle_overrides) {
    const cleanVehicleOverrides: VehicleParamOverrides = {};
    const msrpOverride = clampOverrideValue(sanitized.vehicle_overrides.msrp_override, 0, 10_000_000);
    if (msrpOverride !== undefined) {
      cleanVehicleOverrides.msrp_override = msrpOverride;
    }
    const payloadOverride = clampOverrideValue(sanitized.vehicle_overrides.payload_override, 0, 100);
    if (payloadOverride !== undefined) {
      cleanVehicleOverrides.payload_override = payloadOverride;
    }
    const rangeOverride = clampOverrideValue(sanitized.vehicle_overrides.range_km_override, 50, 2500);
    if (rangeOverride !== undefined) {
      cleanVehicleOverrides.range_km_override = rangeOverride;
    }
    const batteryCapacityOverride = clampOverrideValue(
      sanitized.vehicle_overrides.battery_capacity_kwh_override,
      0,
      2000
    );
    if (batteryCapacityOverride !== undefined) {
      cleanVehicleOverrides.battery_capacity_kwh_override = batteryCapacityOverride;
    }
    const kwhPerKmOverride = clampOverrideValue(
      sanitized.vehicle_overrides.kwh_per_km_override,
      0.1,
      10
    );
    if (kwhPerKmOverride !== undefined) {
      cleanVehicleOverrides.kwh_per_km_override = kwhPerKmOverride;
    }
    const litresPerKmOverride = clampOverrideValue(
      sanitized.vehicle_overrides.litres_per_km_override,
      0.05,
      5
    );
    if (litresPerKmOverride !== undefined) {
      cleanVehicleOverrides.litres_per_km_override = litresPerKmOverride;
    }
    const annualRegistrationOverride = clampOverrideValue(
      sanitized.vehicle_overrides.annual_registration_override,
      0,
      100_000
    );
    if (annualRegistrationOverride !== undefined) {
      cleanVehicleOverrides.annual_registration_override = annualRegistrationOverride;
    }
    const interestRateOverride = clampOverrideValue(
      sanitized.vehicle_overrides.interest_rate_override,
      0,
      0.2
    );
    if (interestRateOverride !== undefined) {
      cleanVehicleOverrides.interest_rate_override = interestRateOverride;
    }
    const chargingTimeOverride = clampOverrideValue(
      sanitized.vehicle_overrides.charging_time_hours_override,
      0.1,
      8
    );
    if (chargingTimeOverride !== undefined) {
      cleanVehicleOverrides.charging_time_hours_override = chargingTimeOverride;
    }
    sanitized.vehicle_overrides = cleanVehicleOverrides;
  }

  return sanitized;
};

const NUMERIC_VEHICLE_FIELDS = [
  'payload',
  'msrp',
  'range_km',
  'battery_capacity_kwh',
  'kwh_per_km',
  'litres_per_km',
  'maintenance_cost_per_km',
  'annual_registration',
  'annual_kms',
] as const;

type NumericVehicleField = (typeof NUMERIC_VEHICLE_FIELDS)[number];

const normalizeVehicleDetail = (
  vehicle: VehicleDetail,
  fallback: VehicleDetail
): VehicleDetail => {
  const next: VehicleDetail = { ...vehicle };
  NUMERIC_VEHICLE_FIELDS.forEach((key) => {
    const value = toFiniteNumber(next[key]);
    if (value !== undefined) {
      next[key] = value as VehicleDetail[NumericVehicleField];
      return;
    }
    const fallbackValue = toFiniteNumber(fallback[key]);
    next[key] = (fallbackValue ?? 0) as VehicleDetail[NumericVehicleField];
  });
  return next;
};

const asNumber = (value: unknown, name: string): number => {
  if (typeof value !== 'number') {
    throw new Error(`Constant ${name} must be numeric.`);
  }
  return value;
};

const VEHICLE_LIFE = asNumber(CONSTANTS.VEHICLE_LIFE, 'VEHICLE_LIFE');
const DISCOUNT_RATE = asNumber(CONSTANTS.DISCOUNT_RATE, 'DISCOUNT_RATE');
const DOWN_PAYMENT_RATE = asNumber(CONSTANTS.DOWN_PAYMENT_RATE, 'DOWN_PAYMENT_RATE');
const FINANCING_TERM = asNumber(CONSTANTS.FINANCING_TERM, 'FINANCING_TERM');
const BASE_INTEREST_RATE = asNumber(CONSTANTS.INTEREST_RATE, 'INTEREST_RATE');
const WORKING_DAYS = asNumber(CONSTANTS.WORKING_DAYS, 'WORKING_DAYS');
const BATTERY_USABLE_RANGE_FACTOR = asNumber(CONSTANTS.BATTERY_USABLE_RANGE_FACTOR, 'BATTERY_USABLE_RANGE_FACTOR');
const HOURLY_WAGE = asNumber(CONSTANTS.HOURLY_WAGE, 'HOURLY_WAGE');
const BATTERY_REPLACEMENT_COST = asNumber(CONSTANTS.BATTERY_REPLACEMENT_COST, 'BATTERY_REPLACEMENT_COST');
const BATTERY_RECYCLE_VALUE = asNumber(CONSTANTS.BATTERY_RECYCLE_VALUE, 'BATTERY_RECYCLE_VALUE');
const BATTERY_LIFE_VARIATION_BASE = asNumber(CONSTANTS.BATTERY_LIFE_VARIATION_BASE, 'BATTERY_LIFE_VARIATION_BASE');
const BATTERY_REPLACEMENT_YEAR = CONSTANTS.BATTERY_REPLACEMENT_YEAR ?? 8;
const DIESEL_PRICE = asNumber(CONSTANTS.DIESEL_PRICE, 'DIESEL_PRICE');
const FUEL_TAX_CREDIT = asNumber(CONSTANTS.FUEL_TAX_CREDIT, 'FUEL_TAX_CREDIT');
const ROAD_USER_CHARGE = asNumber(CONSTANTS.ROAD_USER_CHARGE, 'ROAD_USER_CHARGE');
const DIESEL_EMISSIONS = asNumber(CONSTANTS.DIESEL_EMISSIONS, 'DIESEL_EMISSIONS');
const INSURANCE_RATE_BEV = asNumber(CONSTANTS.INSURANCE_RATE_BEV, 'INSURANCE_RATE_BEV');
const INSURANCE_RATE_DSL = asNumber(CONSTANTS.INSURANCE_RATE_DSL, 'INSURANCE_RATE_DSL');
const OTHER_INSURANCE = asNumber(CONSTANTS.OTHER_INSURANCE, 'OTHER_INSURANCE');
const STAMP_DUTY_RATE = asNumber(CONSTANTS.STAMP_DUTY_RATE, 'STAMP_DUTY_RATE');
const DEPRECIATION_RATE_FIRST_YEAR = asNumber(
  CONSTANTS.DEPRECIATION_RATE_FIRST_YEAR,
  'DEPRECIATION_RATE_FIRST_YEAR'
);
const DEPRECIATION_RATE_ONGOING = asNumber(
  CONSTANTS.DEPRECIATION_RATE_ONGOING,
  'DEPRECIATION_RATE_ONGOING'
);

const MAINTENANCE_COST_PER_KM = assertMaintenanceCosts(CONSTANTS.MAINTENANCE_COST_PER_KM);
const FREIGHT_RATE_PER_TONNE_KM = assertRecord<WeightClass, number>(
  CONSTANTS.FREIGHT_RATE_PER_TONNE_KM,
  'FREIGHT_RATE_PER_TONNE_KM'
);
const PAYLOAD_UTILISATION_FACTOR = assertRecord<WeightClass, number>(
  CONSTANTS.PAYLOAD_UTILISATION_FACTOR,
  'PAYLOAD_UTILISATION_FACTOR'
);
const CHARGING_TIME_HOURS = assertRecord<WeightClass, number>(
  CONSTANTS.CHARGING_TIME_HOURS,
  'CHARGING_TIME_HOURS'
);
const CHARGING_MIX = (CONSTANTS.CHARGING_MIX_PROPORTIONS as { BEV: Record<WeightClass, ChargingMix> }).BEV;

const RETAIL_PRICE = asNumber(CONSTANTS.RETAIL_CHARGING_PRICE, 'RETAIL_CHARGING_PRICE');
const OFFPEAK_PRICE = asNumber(CONSTANTS.OFFPEAK_CHARGING_PRICE, 'OFFPEAK_CHARGING_PRICE');
const SOLAR_PRICE = asNumber(CONSTANTS.SOLAR_CHARGING_PRICE, 'SOLAR_CHARGING_PRICE');
const PUBLIC_PRICE = asNumber(CONSTANTS.PUBLIC_CHARGING_PRICE, 'PUBLIC_CHARGING_PRICE');
const RETAIL_EMISSIONS = asNumber(CONSTANTS.RETAIL_CHARGING_EMISSIONS, 'RETAIL_CHARGING_EMISSIONS');
const OFFPEAK_EMISSIONS = asNumber(CONSTANTS.OFFPEAK_CHARGING_EMISSIONS, 'OFFPEAK_CHARGING_EMISSIONS');
const SOLAR_EMISSIONS = asNumber(CONSTANTS.SOLAR_CHARGING_EMISSIONS, 'SOLAR_CHARGING_EMISSIONS');
const PUBLIC_EMISSIONS = asNumber(CONSTANTS.PUBLIC_CHARGING_EMISSIONS, 'PUBLIC_CHARGING_EMISSIONS');

const getScenario = (scenarioKey: ScenarioKey): EconomicScenarioDefinition => {
  const scenario = SCENARIO_DEFINITIONS[scenarioKey];
  if (!scenario) {
    throw new Error(`Scenario '${scenarioKey}' is not defined.`);
  }
  return scenario;
};

const getVehicle = (vehicleId: string): VehicleDetail => {
  const vehicle = VEHICLE_BY_ID[vehicleId];
  if (!vehicle) {
    throw new Error(
      `Vehicle '${vehicleId}' not found in catalog. ` +
      `Available vehicles: ${Object.keys(VEHICLE_BY_ID).join(', ')}`
    );
  }
  return vehicle;
};

const applyVehicleOverrides = (
  vehicle: VehicleDetail,
  overrides?: VehicleParamOverrides
): VehicleDetail => {
  if (!overrides) {
    return vehicle;
  }

  const next: VehicleDetail = { ...vehicle };
  if (overrides.msrp_override !== undefined) {
    next.msrp = overrides.msrp_override;
  }
  if (overrides.payload_override !== undefined) {
    next.payload = overrides.payload_override;
  }
  if (overrides.range_km_override !== undefined) {
    next.range_km = overrides.range_km_override;
  }
  if (overrides.battery_capacity_kwh_override !== undefined) {
    next.battery_capacity_kwh = overrides.battery_capacity_kwh_override;
  }
  if (overrides.kwh_per_km_override !== undefined) {
    next.kwh_per_km = overrides.kwh_per_km_override;
  }
  if (overrides.litres_per_km_override !== undefined) {
    next.litres_per_km = overrides.litres_per_km_override;
  }
  if (overrides.annual_registration_override !== undefined) {
    next.annual_registration = overrides.annual_registration_override;
  }
  return next;
};

const getSeriesValue = (series: number[] | undefined, year: number, fallback: number): number => {
  if (!series || series.length < year) {
    return fallback;
  }
  return series[year - 1];
};

const dutyCycleToProfile = (dutyCycle?: DutyCycle): ChargingMix => {
  const raw = dutyCycle ?? DEFAULT_DUTY_CYCLE;

  let urban = Number(raw.urban) || 0;
  let regional = Number(raw.regional) || 0;
  let longHaul = Number(raw.longHaul) || 0;

  if (urban < 0) urban = 0;
  if (regional < 0) regional = 0;
  if (longHaul < 0) longHaul = 0;

  let total = urban + regional + longHaul;

  if (total === 0) {
    urban = DEFAULT_DUTY_CYCLE.urban;
    regional = DEFAULT_DUTY_CYCLE.regional;
    longHaul = DEFAULT_DUTY_CYCLE.longHaul;
    total = urban + regional + longHaul;
  }

  const normalized: DutyCycle = {
    urban: (urban / total) * 100,
    regional: (regional / total) * 100,
    longHaul: (longHaul / total) * 100,
  };

  // Route-type profiles. Urban leans on depot/off-peak, long haul leans on public DC.
  const profiles: Record<'urban' | 'regional' | 'longHaul', ChargingMix> = {
    urban: { retail: 0, offpeak: 0.9, public: 0.1, solar: 0 },
    regional: { retail: 0, offpeak: 0.75, public: 0.25, solar: 0 },
    longHaul: { retail: 0, offpeak: 0.35, public: 0.65, solar: 0 },
  };

  const dutyWeighted: ChargingMix = {
    retail:
      (normalized.urban * profiles.urban.retail +
        normalized.regional * profiles.regional.retail +
        normalized.longHaul * profiles.longHaul.retail) /
      100,
    offpeak:
      (normalized.urban * profiles.urban.offpeak +
        normalized.regional * profiles.regional.offpeak +
        normalized.longHaul * profiles.longHaul.offpeak) /
      100,
    public:
      (normalized.urban * profiles.urban.public +
        normalized.regional * profiles.regional.public +
        normalized.longHaul * profiles.longHaul.public) /
      100,
    solar:
      (normalized.urban * profiles.urban.solar +
        normalized.regional * profiles.regional.solar +
        normalized.longHaul * profiles.longHaul.solar) /
      100,
  };

  const totalWeight =
    dutyWeighted.retail + dutyWeighted.offpeak + dutyWeighted.public + dutyWeighted.solar || 1;
  return {
    retail: dutyWeighted.retail / totalWeight,
    offpeak: dutyWeighted.offpeak / totalWeight,
    public: dutyWeighted.public / totalWeight,
    solar: dutyWeighted.solar / totalWeight,
  };
};

const getDutyAdjustedChargingMix = (vehicle: VehicleDetail, dutyCycle?: DutyCycle): ChargingMix => {
  const baseMix = CHARGING_MIX[vehicle.weight_class];
  if (!baseMix) {
    throw new Error(`Missing charging mix for ${vehicle.weight_class}`);
  }

  const dutyProfile = dutyCycleToProfile(dutyCycle);
  const defaultProfile = dutyCycleToProfile(DEFAULT_DUTY_CYCLE);

  const isDefaultDutyCycle =
    Math.abs(dutyProfile.retail - defaultProfile.retail) < 0.0001 &&
    Math.abs(dutyProfile.offpeak - defaultProfile.offpeak) < 0.0001 &&
    Math.abs(dutyProfile.public - defaultProfile.public) < 0.0001 &&
    Math.abs(dutyProfile.solar - defaultProfile.solar) < 0.0001;

  if (isDefaultDutyCycle) {
    return baseMix;
  }

  // Preserve base mix when duty cycle matches the default; otherwise bias toward the duty-driven mix.
  const adjusted: ChargingMix = {
    retail:
      baseMix.retail === 0 || defaultProfile.retail === 0
        ? baseMix.retail
        : baseMix.retail * (dutyProfile.retail / defaultProfile.retail),
    offpeak:
      baseMix.offpeak === 0 || defaultProfile.offpeak === 0
        ? baseMix.offpeak
        : baseMix.offpeak * (dutyProfile.offpeak / defaultProfile.offpeak),
    public:
      baseMix.public === 0 || defaultProfile.public === 0
        ? baseMix.public
        : baseMix.public * (dutyProfile.public / defaultProfile.public),
    solar:
      baseMix.solar === 0 || defaultProfile.solar === 0
        ? baseMix.solar
        : baseMix.solar * (dutyProfile.solar / defaultProfile.solar),
  };

  const total =
    adjusted.retail + adjusted.offpeak + adjusted.public + adjusted.solar || 1;

  return {
    retail: adjusted.retail / total,
    offpeak: adjusted.offpeak / total,
    public: adjusted.public / total,
    solar: adjusted.solar / total,
  };
};

const getChargingBlendRate = (mix: ChargingMix): number => {
  return mix.retail * RETAIL_PRICE + mix.offpeak * OFFPEAK_PRICE + mix.solar * SOLAR_PRICE + mix.public * PUBLIC_PRICE;
};

const getChargingBlendEmissions = (mix: ChargingMix): number => {
  return (
    mix.retail * RETAIL_EMISSIONS +
    mix.offpeak * OFFPEAK_EMISSIONS +
    mix.solar * SOLAR_EMISSIONS +
    mix.public * PUBLIC_EMISSIONS
  );
};

const getMaintenanceBaseCost = (vehicle: VehicleDetail): number => {
  const drivetrainCosts = MAINTENANCE_COST_PER_KM[vehicle.drivetrain_type];
  const costPerKm = drivetrainCosts?.[vehicle.weight_class];
  if (typeof costPerKm !== 'number') {
    throw new Error(`Maintenance rate missing for ${vehicle.drivetrain_type}/${vehicle.weight_class}`);
  }
  return vehicle.annual_kms * costPerKm;
};

const shouldApplyRoadUserChargeToBev = (
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): boolean => {
  if (overrides?.apply_road_user_charge_bev !== true) {
    return false;
  }
  const startYear = scenario.road_user_charge_bev_start_year;
  return startYear === null ? true : year >= startYear;
};

const getBevRoadUserChargeRate = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number
): number => {
  const pairedDiesel = vehicle.comparison_pair ? VEHICLE_BY_ID[vehicle.comparison_pair] : undefined;
  if (!pairedDiesel || pairedDiesel.drivetrain_type !== 'Diesel' || pairedDiesel.litres_per_km <= 0) {
    return 0;
  }
  const efficiencyMultiplier = getSeriesValue(scenario.diesel_efficiency_improvement, year, 1);
  const adjustedLitresPerKm = pairedDiesel.litres_per_km * efficiencyMultiplier;
  return Math.max(0, adjustedLitresPerKm * ROAD_USER_CHARGE);
};

const calculateFuelCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides,
  dutyCycle?: DutyCycle
): number => {
  if (vehicle.drivetrain_type === 'BEV') {
    let efficiencyMultiplier = getSeriesValue(scenario.bev_efficiency_improvement, year, 1);
    if (overrides?.charging_efficiency_variation) {
      efficiencyMultiplier *= overrides.charging_efficiency_variation;
    }
    const adjustedKwhPerKm = vehicle.kwh_per_km * efficiencyMultiplier;
    const chargingMix = getDutyAdjustedChargingMix(vehicle, dutyCycle);
    const baseCost = adjustedKwhPerKm * vehicle.annual_kms * getChargingBlendRate(chargingMix);
    let priceMultiplier = getSeriesValue(scenario.electricity_price_trajectory, year, 1);
    if (overrides?.electricity_price_variation) {
      priceMultiplier *= overrides.electricity_price_variation;
    }
    const electricityCost = baseCost * priceMultiplier;
    const roadUserCharge =
      shouldApplyRoadUserChargeToBev(scenario, year, overrides)
        ? vehicle.annual_kms * getBevRoadUserChargeRate(vehicle, scenario, year)
        : 0;
    return electricityCost + roadUserCharge;
  }

  const efficiencyMultiplier = getSeriesValue(scenario.diesel_efficiency_improvement, year, 1);
  const adjustedLitresPerKm = vehicle.litres_per_km * efficiencyMultiplier;
  const effectiveDieselPrice = Math.max(0, DIESEL_PRICE - FUEL_TAX_CREDIT);
  const baseCost = adjustedLitresPerKm * vehicle.annual_kms * effectiveDieselPrice;
  let priceMultiplier = getSeriesValue(scenario.diesel_price_trajectory, year, 1);
  if (overrides?.fuel_price_variation) {
    priceMultiplier *= overrides.fuel_price_variation;
  }
  return baseCost * priceMultiplier;
};

const calculateBatteryReplacementYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): number => {
  if (vehicle.drivetrain_type !== 'BEV' || vehicle.battery_capacity_kwh <= 0 || year !== BATTERY_REPLACEMENT_YEAR) {
    return 0;
  }
  const multiplier = getSeriesValue(scenario.battery_price_trajectory, year, 1);
  let replacementCost =
    vehicle.battery_capacity_kwh * (BATTERY_REPLACEMENT_COST * multiplier - BATTERY_RECYCLE_VALUE);
  if (overrides?.battery_life_variation !== undefined) {
    replacementCost *= BATTERY_LIFE_VARIATION_BASE - overrides.battery_life_variation;
  }
  return replacementCost;
};

const calculateCarbonCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  dutyCycle?: DutyCycle,
  overrides?: CostOverrides
): number => {
  const carbonPrice = getSeriesValue(scenario.carbon_price_trajectory, year, 0);
  if (carbonPrice === 0) {
    return 0;
  }
  if (vehicle.drivetrain_type === 'BEV') {
    let efficiencyMultiplier = getSeriesValue(scenario.bev_efficiency_improvement, year, 1);
    if (overrides?.charging_efficiency_variation) {
      efficiencyMultiplier *= overrides.charging_efficiency_variation;
    }
    const adjustedKwhPerKm = vehicle.kwh_per_km * efficiencyMultiplier;
    const chargingMix = getDutyAdjustedChargingMix(vehicle, dutyCycle);
    const emissionsRate = getChargingBlendEmissions(chargingMix); // kg CO2e/kWh
    const emissionsTonnes = (adjustedKwhPerKm * vehicle.annual_kms * emissionsRate) / 1000;
    return emissionsTonnes * carbonPrice;
  }

  const efficiencyMultiplier = getSeriesValue(scenario.diesel_efficiency_improvement, year, 1);
  const adjustedLitresPerKm = vehicle.litres_per_km * efficiencyMultiplier;
  const emissionsTonnes = (adjustedLitresPerKm * vehicle.annual_kms * DIESEL_EMISSIONS) / 1000;
  return emissionsTonnes * carbonPrice;
};

const calculateMaintenanceCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): number => {
  let multiplier = getSeriesValue(scenario.maintenance_cost_multiplier, year, 1);
  if (overrides?.maintenance_cost_variation) {
    multiplier *= overrides.maintenance_cost_variation;
  }
  return getMaintenanceBaseCost(vehicle) * multiplier;
};

const calculateChargingLabourCost = (
  vehicle: VehicleDetail,
  chargingTimeOverride?: number
): number => {
  if (vehicle.drivetrain_type !== 'BEV') {
    return 0;
  }
  const dailyKms = vehicle.annual_kms / WORKING_DAYS;
  const usableRange = vehicle.range_km * BATTERY_USABLE_RANGE_FACTOR;
  if (usableRange <= 0) {
    return 0;
  }
  const sessionsPerDay = dailyKms <= usableRange ? 0 : Math.ceil((dailyKms - usableRange) / usableRange);
  const hoursPerDay = chargingTimeOverride ?? CHARGING_TIME_HOURS[vehicle.weight_class] ?? 0;
  if (hoursPerDay <= 0) {
    return 0;
  }
  return sessionsPerDay * hoursPerDay * WORKING_DAYS * HOURLY_WAGE;
};

const calculatePayloadPenalty = (vehicle: VehicleDetail): number => {
  if (!vehicle.comparison_pair) {
    return 0;
  }
  const comparison = VEHICLE_BY_ID[vehicle.comparison_pair];
  if (!comparison) {
    return 0;
  }
  const payloadDifference = comparison.payload - vehicle.payload;
  if (payloadDifference <= 0) {
    return 0;
  }
  const freightRate = FREIGHT_RATE_PER_TONNE_KM[vehicle.weight_class];
  const utilisation = PAYLOAD_UTILISATION_FACTOR[vehicle.weight_class];
  return payloadDifference * freightRate * vehicle.annual_kms * utilisation;
};

const calculateStampDuty = (msrp: number, isBev: boolean): number => {
  const baseDuty = msrp * STAMP_DUTY_RATE;
  const stampPolicy = POLICY_CONFIG.stamp_duty_exemption;
  if (isBev && stampPolicy?.enabled) {
    const exemption = stampPolicy.exemption_percentage ?? 0;
    return baseDuty * (1 - exemption);
  }
  return baseDuty;
};

const calculateBevPurchaseRebate = (msrp: number): number => {
  let rebate = 0;
  const fixedPolicy = POLICY_CONFIG.purchase_rebate;
  const percentagePolicy = POLICY_CONFIG.percentage_rebate;
  if (fixedPolicy?.enabled) {
    rebate += fixedPolicy.amount ?? 0;
  }
  if (percentagePolicy?.enabled) {
    // Apply fixed rebate before calculating percentage rebate.
    const percentageBase = Math.max(0, msrp - rebate);
    let percentage = percentageBase * (percentagePolicy.percentage ?? 0);
    if (percentagePolicy.max_amount) {
      percentage = Math.min(percentage, percentagePolicy.max_amount);
    }
    rebate += percentage;
  }
  return rebate;
};

const calculateInitialCost = (vehicle: VehicleDetail) => {
  const isBev = vehicle.drivetrain_type === 'BEV';
  const stampDuty = calculateStampDuty(vehicle.msrp, isBev);
  const rebate = isBev ? calculateBevPurchaseRebate(vehicle.msrp) : 0;
  return {
    stampDuty,
    rebate,
    initialCost: vehicle.msrp + stampDuty - rebate,
  };
};

const buildFinancingSnapshot = (
  initialCost: number,
  isBev: boolean,
  purchaseMethod: PurchaseMethod,
  interestRateOverride?: number
) => {
  if (purchaseMethod === 'outright') {
    return {
      upfrontCost: initialCost,
      financingCost: 0,
      monthlyPayment: 0,
      npvPurchasePayments: initialCost,
    };
  }

  const downPayment = initialCost * DOWN_PAYMENT_RATE;
  const loanAmount = initialCost - downPayment;
  let interestRate = BASE_INTEREST_RATE;
  const loanPolicy = POLICY_CONFIG.green_loan_subsidy;
  if (isBev && loanPolicy?.enabled) {
    interestRate = Math.max(0, interestRate - (loanPolicy.rate_reduction ?? 0));
  }
  const effectiveRate =
    typeof interestRateOverride === 'number' ? interestRateOverride : interestRate;
  const monthlyRate = effectiveRate / 12;
  const numPayments = FINANCING_TERM * 12;
  const monthlyPayment =
    monthlyRate === 0
      ? loanAmount / numPayments
      : (loanAmount * monthlyRate) / (1 - (1 + monthlyRate) ** -numPayments);
  const totalPayments = monthlyPayment * numPayments;
  const financingCost = totalPayments - loanAmount;
  const npvPayments = calculateNpvOfPayments(monthlyPayment, numPayments, DISCOUNT_RATE) + downPayment;

  return {
    upfrontCost: downPayment,
    financingCost,
    monthlyPayment,
    npvPurchasePayments: npvPayments,
  };
};

const calculateResidualValueAtLife = (
  msrp: number,
  scenario: EconomicScenarioDefinition,
  isBev: boolean,
  overrides?: CostOverrides
) => {
  const firstYearDep = msrp * DEPRECIATION_RATE_FIRST_YEAR;
  let residual = msrp - firstYearDep;
  for (let year = 2; year <= VEHICLE_LIFE; year += 1) {
    residual *= 1 - DEPRECIATION_RATE_ONGOING;
  }
  if (isBev) {
    residual *= getSeriesValue(scenario.bev_residual_value_multiplier, VEHICLE_LIFE, 1);
  }
  if (overrides?.residual_value_variation) {
    residual *= overrides.residual_value_variation;
  }
  return {
    residualFuture: residual,
    depreciation: msrp - residual,
  };
};

const getAnnualInsuranceCost = (vehicle: VehicleDetail): number => {
  const rate = vehicle.drivetrain_type === 'BEV' ? INSURANCE_RATE_BEV : INSURANCE_RATE_DSL;
  return vehicle.msrp * rate + OTHER_INSURANCE;
};

export const calculateTco = (payload: CalculationRequestPayload): CalculationResponsePayload => {
  // Sanitize payload to prevent NaN and invalid values
  const sanitizedPayload = sanitizePayload(payload);

  const baseVehicle = getVehicle(sanitizedPayload.vehicle_id);
  const scenario = getScenario(sanitizedPayload.scenario_name);
  const overrides = sanitizedPayload.overrides;
  const dutyCycle = sanitizedPayload.duty_cycle ?? DEFAULT_DUTY_CYCLE;
  const vehicleWithStructuralOverrides = applyVehicleOverrides(
    baseVehicle,
    sanitizedPayload.vehicle_overrides
  );
  const annualKms =
    overrides?.annual_kms_variation && overrides.annual_kms_variation > 0
      ? overrides.annual_kms_variation
      : vehicleWithStructuralOverrides.annual_kms;
  const vehicle = normalizeVehicleDetail(
    {
      ...vehicleWithStructuralOverrides,
      annual_kms: annualKms,
    },
    baseVehicle
  );
  const isBev = vehicle.drivetrain_type === 'BEV';

  const { stampDuty, initialCost } = calculateInitialCost(vehicle);
  const financing = buildFinancingSnapshot(
    initialCost,
    isBev,
    sanitizedPayload.purchase_method,
    sanitizedPayload.vehicle_overrides?.interest_rate_override
  );
  const annualInsuranceCost = getAnnualInsuranceCost(vehicle);
  const annualChargingLabourCost = calculateChargingLabourCost(
    vehicle,
    sanitizedPayload.vehicle_overrides?.charging_time_hours_override
  );
  const annualPayloadPenalty = calculatePayloadPenalty(vehicle);

  const annualFuelCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateFuelCostYear(vehicle, scenario, idx + 1, overrides, dutyCycle)
  );
  const annualBatteryCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateBatteryReplacementYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualCarbonCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateCarbonCostYear(vehicle, scenario, idx + 1, dutyCycle, overrides)
  );
  const annualMaintenanceCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateMaintenanceCostYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualChargingLabourCosts = Array.from({ length: VEHICLE_LIFE }, () => annualChargingLabourCost);
  const annualPayloadPenalties = Array.from({ length: VEHICLE_LIFE }, () => annualPayloadPenalty);

  const totalFuelCost = calculateNpvOfAnnualCashflows(annualFuelCosts, DISCOUNT_RATE);
  const totalBatteryCost = calculateNpvOfAnnualCashflows(annualBatteryCosts, DISCOUNT_RATE);
  const totalCarbonCost = calculateNpvOfAnnualCashflows(annualCarbonCosts, DISCOUNT_RATE);
  const totalMaintenanceCost = calculateNpvOfAnnualCashflows(annualMaintenanceCosts, DISCOUNT_RATE);
  const totalChargingLabourCost = calculateNpvOfAnnualCashflows(annualChargingLabourCosts, DISCOUNT_RATE);
  const totalPayloadPenalty = calculateNpvOfAnnualCashflows(annualPayloadPenalties, DISCOUNT_RATE);

  const insurancePv = calculatePresentValue(annualInsuranceCost, VEHICLE_LIFE, DISCOUNT_RATE);
  const registrationPv = calculatePresentValue(vehicle.annual_registration, VEHICLE_LIFE, DISCOUNT_RATE);

  const { residualFuture, depreciation } = calculateResidualValueAtLife(
    vehicle.msrp,
    scenario,
    isBev,
    overrides
  );
  const residualValuePv = discountToPresent(residualFuture, VEHICLE_LIFE, DISCOUNT_RATE);

  const totalCost =
    financing.npvPurchasePayments +
    totalFuelCost +
    totalMaintenanceCost +
    insurancePv +
    registrationPv +
    totalBatteryCost +
    totalCarbonCost +
    totalChargingLabourCost +
    totalPayloadPenalty -
    residualValuePv;

  const annualCost = calculateAnnualisedCost(totalCost, VEHICLE_LIFE, DISCOUNT_RATE);
  const costPerKm = vehicle.annual_kms > 0 ? annualCost / vehicle.annual_kms : 0;

  const taxesAndFees = stampDuty;

  const breakdown: CostBreakdown = {
    purchase_cost: financing.upfrontCost,
    fuel_cost: totalFuelCost,
    maintenance_cost: totalMaintenanceCost,
    insurance_cost: annualInsuranceCost * VEHICLE_LIFE,
    registration_cost: vehicle.annual_registration * VEHICLE_LIFE,
    battery_replacement_cost: totalBatteryCost,
    financing_cost: financing.financingCost,
    carbon_cost: totalCarbonCost,
    charging_labour_cost: totalChargingLabourCost,
    payload_penalty_cost: totalPayloadPenalty,
    residual_value: residualValuePv,
    depreciation,
    taxes_and_fees: taxesAndFees,
  };

  return {
    vehicle_id: vehicle.vehicle_id,
    scenario_name: scenario.name,
    total_cost: totalCost,
    annual_cost: annualCost,
    cost_per_km: costPerKm,
    breakdown,
  };
};

export const calculateComparison = (
  payload: ComparisonRequestPayload
): CalculationResponsePayload[] => {
  return payload.vehicle_ids.map((vehicleId) =>
    calculateTco({
      vehicle_id: vehicleId,
      scenario_name: payload.scenario_name,
      purchase_method: payload.purchase_method,
      duty_cycle: payload.duty_cycle,
      overrides: payload.overrides,
      vehicle_overrides: payload.vehicle_param_overrides?.[vehicleId],
    })
  );
};

/**
 * Returns a snapshot of the vehicle catalog including version for cache invalidation.
 * @returns Object with version string and vehicles array
 */
export const getVehicleCatalogSnapshot = () => ({
  version: VEHICLE_CATALOG_VERSION,
  vehicles: VEHICLE_DETAILS,
});
