import { describe, expect, it } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { CONSTANTS } from '@shared/data/constants';
import { POLICY_CONFIG } from '@shared/data/policies';
import { VEHICLE_BY_ID } from '@shared/data/vehicleCatalog';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Policy rebate interactions', () => {
  it('applies fixed rebate before percentage rebate for BEVs', () => {
    const purchasePolicy = POLICY_CONFIG.purchase_rebate;
    const percentagePolicy = POLICY_CONFIG.percentage_rebate;

    const originalState = {
      purchaseEnabled: purchasePolicy.enabled,
      purchaseAmount: purchasePolicy.amount,
      percentageEnabled: percentagePolicy.enabled,
      percentageRate: percentagePolicy.percentage,
      percentageCap: percentagePolicy.max_amount,
    };

    try {
      purchasePolicy.enabled = true;
      purchasePolicy.amount = 20_000;
      percentagePolicy.enabled = true;
      percentagePolicy.percentage = 0.10;
      percentagePolicy.max_amount = null;

      const payload: CalculationRequestPayload = {
        vehicle_id: 'BEV001',
        scenario_name: 'baseline',
        purchase_method: 'outright',
        duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
      };

      const result = calculateTco(payload);

      const msrp = VEHICLE_BY_ID.BEV001.msrp;
      const stampDutyRate = CONSTANTS.STAMP_DUTY_RATE as number;
      const stampDuty = msrp * stampDutyRate;
      const expectedRebate = 20_000 + (msrp - 20_000) * 0.10;
      const expectedPurchaseCost = msrp + stampDuty - expectedRebate;
      const fullBasePurchaseCost = msrp + stampDuty - (20_000 + msrp * 0.10);

      expect(result.breakdown.upfront_costs.purchase_cost).toBeCloseTo(
        expectedPurchaseCost,
        6
      );
      expect(result.breakdown.upfront_costs.purchase_cost).not.toBeCloseTo(
        fullBasePurchaseCost,
        6
      );
    } finally {
      purchasePolicy.enabled = originalState.purchaseEnabled;
      purchasePolicy.amount = originalState.purchaseAmount;
      percentagePolicy.enabled = originalState.percentageEnabled;
      percentagePolicy.percentage = originalState.percentageRate;
      percentagePolicy.max_amount = originalState.percentageCap;
    }
  });
});
