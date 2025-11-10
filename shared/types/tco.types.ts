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

export interface CalculationRequestPayload {
  vehicle_id: string;
  scenario_name: ScenarioKey;
  purchase_method: PurchaseMethod;
  overrides?: CostOverrides;
}

export interface CostBreakdown {
  purchase_cost: number;
  fuel_cost: number;
  maintenance_cost: number;
  insurance_cost: number;
  registration_cost: number;
  battery_replacement_cost: number;
  financing_cost: number;
  carbon_cost: number;
  charging_labour_cost: number;
  payload_penalty_cost: number;
  residual_value: number;
  depreciation: number;
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
  overrides?: CostOverrides;
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

export interface AnalyticsSummaryPayload {
  totalSessions: number;
  completedSessions: number;
  calculationsLast24h: number;
  bevWinRate?: number | null;
  averagePaybackYears?: number | null;
  averageCostDelta?: number | null;
  topVehicles: Record<string, number>;
}

export interface ApiError {
  detail: string;
}
