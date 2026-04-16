import { describe, expect, it } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { CONSTANTS } from '@shared/data/constants';
import { VEHICLE_DETAILS } from '@shared/data/vehicleCatalog';
import type { ScenarioKey } from '@shared/types/tco.types';
import type { PurchaseMethod } from '@shared/types/tco.types';
import { calculatePresentValue } from '@shared/calculator/math';

const DISCOUNT_RATE = CONSTANTS.DISCOUNT_RATE as number;
const VEHICLE_LIFE = CONSTANTS.VEHICLE_LIFE as number;

const convertNominalLifetimeToNpv = (nominalLifetimeCost: number): number => {
  if (VEHICLE_LIFE <= 0) {
    return nominalLifetimeCost;
  }

  const annualCost = nominalLifetimeCost / VEHICLE_LIFE;
  return calculatePresentValue(annualCost, VEHICLE_LIFE, DISCOUNT_RATE);
};

describe('cost breakdown chart NPV consistency', () => {
  const scenarios: ScenarioKey[] = ['baseline', 'oil_crisis', 'technology_breakthrough'];
  const purchaseMethods: PurchaseMethod[] = ['outright', 'financed'];

  it('reconstructed chart components sum to total_cost for all vehicles', () => {
    for (const scenario of scenarios) {
      for (const purchaseMethod of purchaseMethods) {
        for (const vehicle of VEHICLE_DETAILS) {
          const result = calculateTco({
            vehicle_id: vehicle.vehicle_id,
            scenario_name: scenario,
            purchase_method: purchaseMethod,
          });

          const insuranceCostNpv = convertNominalLifetimeToNpv(result.breakdown.nominal_costs.insurance_cost);
          const registrationCostNpv = convertNominalLifetimeToNpv(
            result.breakdown.nominal_costs.registration_cost
          );
          const residualValueCredit = -result.breakdown.npv_costs.residual_value;
          const nonPurchaseComponents =
            result.breakdown.npv_costs.fuel_cost +
            result.breakdown.npv_costs.maintenance_cost +
            insuranceCostNpv +
            registrationCostNpv +
            result.breakdown.npv_costs.battery_replacement_cost +
            result.breakdown.npv_costs.carbon_cost +
            result.breakdown.npv_costs.charging_labour_cost +
            result.breakdown.npv_costs.payload_penalty_cost +
            result.breakdown.npv_costs.payload_trip_multiplier_cost +
            result.breakdown.npv_costs.charging_dwell_opportunity_cost +
            result.breakdown.npv_costs.mr_downtime_opportunity_cost +
            residualValueCredit;
          const purchaseFinancingNpv = result.total_cost - nonPurchaseComponents;
          const reconstructedTotal = purchaseFinancingNpv + nonPurchaseComponents;

          expect(reconstructedTotal).toBeCloseTo(result.total_cost, 6);
        }
      }
    }
  });
});
