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
  apply_road_user_charge_bev?: boolean;
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

export interface NpvCostBreakdown {
  /** NPV of fuel/energy costs over vehicle life */
  fuel_cost: number;
  /** NPV of maintenance costs over vehicle life */
  maintenance_cost: number;
  /** NPV of battery replacement cost (if applicable) */
  battery_replacement_cost: number;
  /** NPV of carbon cost over vehicle life */
  carbon_cost: number;
  /** NPV of charging labour cost (driver time at charger) */
  charging_labour_cost: number;
  /** NPV of payload penalty (lost revenue from reduced capacity) */
  payload_penalty_cost: number;
  /** NPV of residual value at end of life (negative value - offsets costs) */
  residual_value: number;
}

export interface NominalCostBreakdown {
  /** Nominal total: annual insurance × vehicle life (NOT NPV-adjusted) */
  insurance_cost: number;
  /** Nominal total: annual registration × vehicle life (NOT NPV-adjusted) */
  registration_cost: number;
  /** Total nominal interest paid over loan term (NOT NPV-adjusted) */
  financing_cost: number;
  /** Accounting depreciation: MSRP minus residual value */
  depreciation: number;
}

export interface UpfrontCostBreakdown {
  /** Upfront purchase price including stamp duty, minus rebates */
  purchase_cost: number;
  /** Stamp duty only (registration is separate in registration_cost) */
  taxes_and_fees: number;
}

/**
 * Grouped cost breakdown for a vehicle over its lifetime.
 *
 * NOTE: The `total_cost` in `CalculationResponsePayload` is fully NPV-adjusted
 * and is the authoritative comparison metric.
 */
export interface CostBreakdown {
  npv_costs: NpvCostBreakdown;
  nominal_costs: NominalCostBreakdown;
  upfront_costs: UpfrontCostBreakdown;
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

export type SessionCreateResponsePayload = SessionResponsePayload;

export type SessionUpdatePayload = Partial<SessionCreatePayload>;

export interface ApiError {
  detail: string;
}
