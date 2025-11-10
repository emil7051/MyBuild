import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
  CostBreakdown,
  CostOverrides,
  EconomicScenarioDefinition,
  PurchaseMethod,
  ScenarioKey,
  VehicleDetail,
  VehicleParamOverrides,
} from '../types/tco.types';
import { VEHICLE_BY_ID, VEHICLE_DETAILS } from '../data/vehicleCatalog';
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
const DIESEL_PRICE = asNumber(CONSTANTS.DIESEL_PRICE, 'DIESEL_PRICE');
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

const MAINTENANCE_COST_PER_KM = CONSTANTS.MAINTENANCE_COST_PER_KM as Record<
  'BEV' | 'Diesel',
  Record<WeightClass, number>
>;
const FREIGHT_RATE_PER_TONNE_KM = CONSTANTS.FREIGHT_RATE_PER_TONNE_KM as Record<WeightClass, number>;
const PAYLOAD_UTILISATION_FACTOR = CONSTANTS.PAYLOAD_UTILISATION_FACTOR as Record<WeightClass, number>;
const CHARGING_TIME_HOURS = CONSTANTS.CHARGING_TIME_HOURS as Record<WeightClass, number>;
const CHARGING_MIX = (CONSTANTS.CHARGING_MIX_PROPORTIONS as { BEV: Record<WeightClass, ChargingMix> }).BEV;

const RETAIL_PRICE = asNumber(CONSTANTS.RETAIL_CHARGING_PRICE, 'RETAIL_CHARGING_PRICE');
const OFFPEAK_PRICE = asNumber(CONSTANTS.OFFPEAK_CHARGING_PRICE, 'OFFPEAK_CHARGING_PRICE');
const SOLAR_PRICE = asNumber(CONSTANTS.SOLAR_CHARGING_PRICE, 'SOLAR_CHARGING_PRICE');
const PUBLIC_PRICE = asNumber(CONSTANTS.PUBLIC_CHARGING_PRICE, 'PUBLIC_CHARGING_PRICE');

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
    throw new Error(`Vehicle '${vehicleId}' not found.`);
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

const getChargingBlendRate = (vehicle: VehicleDetail): number => {
  const mix = CHARGING_MIX[vehicle.weight_class];
  if (!mix) {
    throw new Error(`Missing charging mix for ${vehicle.weight_class}`);
  }
  return (
    mix.retail * RETAIL_PRICE +
    mix.offpeak * OFFPEAK_PRICE +
    mix.solar * SOLAR_PRICE +
    mix.public * PUBLIC_PRICE
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

const calculateFuelCostYear = (
  vehicle: VehicleDetail,
  scenario: EconomicScenarioDefinition,
  year: number,
  overrides?: CostOverrides
): number => {
  if (vehicle.drivetrain_type === 'BEV') {
    let efficiencyMultiplier = getSeriesValue(scenario.bev_efficiency_improvement, year, 1);
    if (overrides?.charging_efficiency_variation) {
      efficiencyMultiplier *= overrides.charging_efficiency_variation;
    }
    const adjustedKwhPerKm = vehicle.kwh_per_km * efficiencyMultiplier;
    const baseCost = adjustedKwhPerKm * vehicle.annual_kms * getChargingBlendRate(vehicle);
    let priceMultiplier = getSeriesValue(scenario.electricity_price_trajectory, year, 1);
    if (overrides?.electricity_price_variation) {
      priceMultiplier *= overrides.electricity_price_variation;
    }
    return baseCost * priceMultiplier;
  }

  const efficiencyMultiplier = getSeriesValue(scenario.diesel_efficiency_improvement, year, 1);
  const adjustedLitresPerKm = vehicle.litres_per_km * efficiencyMultiplier;
  const baseCost = adjustedLitresPerKm * vehicle.annual_kms * DIESEL_PRICE;
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
  if (vehicle.drivetrain_type !== 'BEV' || vehicle.battery_capacity_kwh <= 0 || year !== 8) {
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
  year: number
): number => {
  if (vehicle.drivetrain_type === 'BEV') {
    return 0;
  }
  const carbonPrice = getSeriesValue(scenario.carbon_price_trajectory, year, 0);
  if (carbonPrice === 0) {
    return 0;
  }
  const emissionsTonnes = (vehicle.litres_per_km * vehicle.annual_kms * DIESEL_EMISSIONS) / 1000;
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
  const sessionsPerDay = dailyKms <= usableRange ? 0 : Math.ceil((dailyKms - usableRange) / usableRange);
  const hoursPerDay = chargingTimeOverride ?? CHARGING_TIME_HOURS[vehicle.weight_class] ?? 0;
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
    let percentage = msrp * (percentagePolicy.percentage ?? 0);
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
  initialCost: number,
  scenario: EconomicScenarioDefinition,
  isBev: boolean,
  overrides?: CostOverrides
) => {
  const firstYearDep = initialCost * DEPRECIATION_RATE_FIRST_YEAR;
  let residual = initialCost - firstYearDep;
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
    depreciation: initialCost - residual,
  };
};

const getAnnualInsuranceCost = (vehicle: VehicleDetail): number => {
  const rate = vehicle.drivetrain_type === 'BEV' ? INSURANCE_RATE_BEV : INSURANCE_RATE_DSL;
  return vehicle.msrp * rate + OTHER_INSURANCE;
};

const getAnnualKms = (vehicle: VehicleDetail, overrides?: CostOverrides): number => {
  if (overrides?.annual_kms_variation && overrides.annual_kms_variation > 0) {
    return overrides.annual_kms_variation;
  }
  return vehicle.annual_kms;
};

export const calculateTco = (payload: CalculationRequestPayload): CalculationResponsePayload => {
  const baseVehicle = getVehicle(payload.vehicle_id);
  const vehicle = applyVehicleOverrides(baseVehicle, payload.vehicle_overrides);
  const scenario = getScenario(payload.scenario_name);
  const overrides = payload.overrides;
  const isBev = vehicle.drivetrain_type === 'BEV';

  const { stampDuty, initialCost } = calculateInitialCost(vehicle);
  const financing = buildFinancingSnapshot(
    initialCost,
    isBev,
    payload.purchase_method,
    payload.vehicle_overrides?.interest_rate_override
  );
  const annualInsuranceCost = getAnnualInsuranceCost(vehicle);
  const annualChargingLabourCost = calculateChargingLabourCost(
    vehicle,
    payload.vehicle_overrides?.charging_time_hours_override
  );
  const annualPayloadPenalty = calculatePayloadPenalty(vehicle);

  const annualFuelCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateFuelCostYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualBatteryCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateBatteryReplacementYear(vehicle, scenario, idx + 1, overrides)
  );
  const annualCarbonCosts = Array.from({ length: VEHICLE_LIFE }, (_, idx) =>
    calculateCarbonCostYear(vehicle, scenario, idx + 1)
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
    initialCost,
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
  const annualKms = getAnnualKms(vehicle, overrides);
  const costPerKm = annualKms > 0 ? annualCost / annualKms : 0;

  const taxesAndFees = stampDuty + vehicle.annual_registration * VEHICLE_LIFE;

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
      overrides: payload.overrides,
      vehicle_overrides: payload.vehicle_param_overrides?.[vehicleId],
    })
  );
};

export const getVehicleCatalogSnapshot = () => VEHICLE_DETAILS;
