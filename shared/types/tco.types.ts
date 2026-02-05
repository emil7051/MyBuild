/**
 * @file TCO Type Definitions
 * @module shared/types/tco.types
 *
 * TypeScript interfaces and types for the TCO calculator.
 * Defines vehicle specifications, scenarios, calculation inputs/outputs,
 * and wizard state structures.
 */

export type ScenarioKey = 'baseline' | 'technology_breakthrough' | 'oil_crisis';
export type PurchaseMethod = 'financed' | 'outright';

type Primitive = string | number | boolean | null;
type NestedValue = Primitive | NestedValue[] | { [key: string]: NestedValue };
export type ConstantCatalog = Record<string, NestedValue>;

export interface EconomicScenarioDefinition {
  key: string;
  name: string;
  description: string;
  diesel_price_trajectory: number[];
  electricity_price_trajectory: number[];
  battery_price_trajectory: number[];
  carbon_price_trajectory: number[];
  bev_efficiency_improvement: number[];
  diesel_efficiency_improvement: number[];
  maintenance_cost_multiplier: number[];
  bev_residual_value_multiplier: number[];
  infrastructure_cost_trajectory: number[];
  policy_phase_out_year: number | null;
  road_user_charge_bev_start_year: number | null;
}

export type ScenarioDefinitionMap = Record<ScenarioKey, EconomicScenarioDefinition>;

export interface PolicyDefinition {
  name: string;
  description: string;
  enabled: boolean;
  policy_type: string;
  amount?: number | null;
  percentage?: number | null;
  max_amount?: number | null;
  exemption_percentage?: number | null;
  price_per_tonne?: number | null;
  rate_reduction?: number | null;
  grant_percentage?: number | null;
}

export type PolicyCatalog = Record<string, PolicyDefinition>;

export interface CostOverrides {
  annual_kms_variation?: number;
  residual_value_variation?: number;
  fuel_price_variation?: number;
  electricity_price_variation?: number;
  maintenance_cost_variation?: number;
  battery_life_variation?: number;
  charging_efficiency_variation?: number;
}

export interface VehicleParamOverrides {
  msrp_override?: number;
  payload_override?: number;
  range_km_override?: number;
  battery_capacity_kwh_override?: number;
  kwh_per_km_override?: number;
  litres_per_km_override?: number;
  annual_registration_override?: number;
  interest_rate_override?: number;
  charging_time_hours_override?: number;
}

export interface CalculationRequestPayload {
  vehicle_id: string;
  scenario_name: ScenarioKey;
  purchase_method: PurchaseMethod;
  duty_cycle?: DutyCycle;
  overrides?: CostOverrides;
  vehicle_overrides?: VehicleParamOverrides;
}

/**
 * Cost breakdown for a vehicle over its lifetime.
 *
 * IMPORTANT: Value types are MIXED for different cost categories.
 * When displaying or comparing these values, be aware of their different bases.
 *
 * NPV-ADJUSTED (discounted to present value using annuity-due convention):
 * - fuel_cost: Energy/fuel costs over 15 years
 * - maintenance_cost: Maintenance costs over 15 years
 * - battery_replacement_cost: Battery replacement at mid-life (if applicable)
 * - carbon_cost: Carbon price costs over 15 years
 * - charging_labour_cost: Driver time spent charging (BEV only)
 * - payload_penalty_cost: Lost revenue from reduced payload capacity
 * - residual_value: End-of-life vehicle value (negative - offsets costs)
 *
 * NOMINAL LIFETIME TOTALS (NOT discounted - simple sum over 15 years):
 * - insurance_cost: Total insurance premiums (annual × 15)
 * - registration_cost: Total registration fees (annual × 15)
 * - depreciation: Accounting depreciation (MSRP - residual)
 *
 * UPFRONT VALUES (year 0, no discounting needed):
 * - purchase_cost: Initial purchase price including stamp duty, minus rebates
 * - financing_cost: Total nominal interest over loan term (if financed)
 * - taxes_and_fees: Stamp duty and transfer fees (upfront only)
 *
 * NOTE: The total_cost in CalculationResponsePayload IS fully NPV-adjusted
 * and represents the true economic cost comparison. Individual breakdown
 * components should be used for directional insights rather than precise
 * summation due to the mixed value bases.
 */
export interface CostBreakdown {
  /** Upfront purchase price including stamp duty, minus rebates */
  purchase_cost: number;
  /** NPV of fuel/energy costs over vehicle life */
  fuel_cost: number;
  /** NPV of maintenance costs over vehicle life */
  maintenance_cost: number;
  /** Nominal total: annual insurance × vehicle life (NOT NPV-adjusted) */
  insurance_cost: number;
  /** Nominal total: annual registration × vehicle life (NOT NPV-adjusted) */
  registration_cost: number;
  /** NPV of battery replacement cost (if applicable) */
  battery_replacement_cost: number;
  /** Total nominal interest paid over loan term (NOT NPV-adjusted) */
  financing_cost: number;
  /** NPV of carbon cost over vehicle life */
  carbon_cost: number;
  /** NPV of charging labour cost (driver time at charger) */
  charging_labour_cost: number;
  /** NPV of payload penalty (lost revenue from reduced capacity) */
  payload_penalty_cost: number;
  /** NPV of residual value at end of life (negative value - offsets costs) */
  residual_value: number;
  /** Accounting depreciation: MSRP minus residual value */
  depreciation: number;
  /** Stamp duty only (registration is separate in registration_cost) */
  taxes_and_fees: number;
}

export interface CalculationResponsePayload {
  vehicle_id: string;
  scenario_name: ScenarioKey | string;
  total_cost: number;
  annual_cost: number;
  cost_per_km: number;
  breakdown: CostBreakdown;
}

export interface ComparisonRequestPayload {
  vehicle_ids: string[];
  scenario_name: ScenarioKey;
  purchase_method: PurchaseMethod;
  duty_cycle?: DutyCycle;
  overrides?: CostOverrides;
  vehicle_param_overrides?: Record<string, VehicleParamOverrides>;
}

export interface VehicleSummary {
  vehicle_id: string;
  model_name: string;
  drivetrain_type: 'BEV' | 'Diesel';
  weight_class: 'Light Rigid' | 'Medium Rigid' | 'Articulated';
  comparison_pair: string;
}

export interface VehicleDetail extends VehicleSummary {
  payload: number;
  msrp: number;
  range_km: number;
  battery_capacity_kwh: number;
  kwh_per_km: number;
  litres_per_km: number;
  maintenance_cost_per_km: number;
  annual_registration: number;
  annual_kms: number;
}

export interface DutyCycle {
  urban: number;
  regional: number;
  longHaul: number;
}

export interface WizardData {
  currentVehicle?: string;
  comparisonVehicles: string[];
  scenario: ScenarioKey;
  purchaseMethod: PurchaseMethod;
  dutyCycle: DutyCycle;
  overrides?: CostOverrides;
  vehicleParamOverrides?: Record<string, VehicleParamOverrides>;
}

export interface OperatorProfilePayload {
  operatorType?: string;
  fleetSize?: string;
  contactEmail?: string;
  consentToContact?: boolean;
  notes?: string;
}

export interface FeedbackPayload {
  rating?: number;
  comment?: string;
}

export interface SessionCreatePayload {
  wizardData: WizardData;
  results?: CalculationResponsePayload[];
  operatorProfile?: OperatorProfilePayload;
  feedback?: FeedbackPayload;
}

export interface SessionResponsePayload extends SessionCreatePayload {
  sessionId: string;
  status: 'draft' | 'completed';
  updatedAt: string;
  lastCalculatedAt?: string | null;
}

export type SessionUpdatePayload = Partial<SessionCreatePayload>;

export interface ApiError {
  detail: string;
}
