import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import verificationData from '@shared/calculator/verification_data.json';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

// Tolerance for floating point comparisons
// Some small differences are expected due to float precision differences between Python and JS
const TOLERANCE = 0.01; // 1 cent tolerance

describe('TCO Calculation Verification', () => {
  verificationData.forEach((testCase) => {
    it(`should match Python results for ${testCase.id}`, () => {
      const input = testCase.input as unknown as CalculationRequestPayload;
      const expected = testCase.expected;

      const result = calculateTco(input);

      // Verify top-level metrics
      expect(result.total_cost).toBeCloseTo(expected.total_cost, 1); // Lower precision for total cost due to accumulation
      expect(result.annual_cost).toBeCloseTo(expected.annual_cost, 1);
      expect(result.cost_per_km).toBeCloseTo(expected.cost_per_km, 3);

      // Verify breakdown
      expect(result.breakdown.purchase_cost).toBeCloseTo(expected.breakdown.purchase_cost, 1);
      expect(result.breakdown.fuel_cost).toBeCloseTo(expected.breakdown.fuel_cost, 1);
      expect(result.breakdown.maintenance_cost).toBeCloseTo(expected.breakdown.maintenance_cost, 1);
      expect(result.breakdown.insurance_cost).toBeCloseTo(expected.breakdown.insurance_cost, 1);
      expect(result.breakdown.registration_cost).toBeCloseTo(expected.breakdown.registration_cost, 1);
      expect(result.breakdown.battery_replacement_cost).toBeCloseTo(expected.breakdown.battery_replacement_cost, 1);
      expect(result.breakdown.financing_cost).toBeCloseTo(expected.breakdown.financing_cost, 1);
      expect(result.breakdown.carbon_cost).toBeCloseTo(expected.breakdown.carbon_cost, 1);
      expect(result.breakdown.charging_labour_cost).toBeCloseTo(expected.breakdown.charging_labour_cost, 1);
      expect(result.breakdown.payload_penalty_cost).toBeCloseTo(expected.breakdown.payload_penalty_cost, 1);
      expect(result.breakdown.residual_value).toBeCloseTo(expected.breakdown.residual_value, 1);
      expect(result.breakdown.depreciation).toBeCloseTo(expected.breakdown.depreciation, 1);
      expect(result.breakdown.taxes_and_fees).toBeCloseTo(expected.breakdown.taxes_and_fees, 1);
    });
  });
});
