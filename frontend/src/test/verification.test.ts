import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import verificationData from '@shared/calculator/verification_data.json';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

// Tolerance for floating point comparisons is handled by vitest's toBeCloseTo

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
      expect(result.breakdown.upfront_costs.purchase_cost).toBeCloseTo(expected.breakdown.upfront_costs.purchase_cost, 1);
      expect(result.breakdown.npv_costs.fuel_cost).toBeCloseTo(expected.breakdown.npv_costs.fuel_cost, 1);
      expect(result.breakdown.npv_costs.maintenance_cost).toBeCloseTo(expected.breakdown.npv_costs.maintenance_cost, 1);
      expect(result.breakdown.nominal_costs.insurance_cost).toBeCloseTo(expected.breakdown.nominal_costs.insurance_cost, 1);
      expect(result.breakdown.nominal_costs.registration_cost).toBeCloseTo(expected.breakdown.nominal_costs.registration_cost, 1);
      expect(result.breakdown.npv_costs.battery_replacement_cost).toBeCloseTo(expected.breakdown.npv_costs.battery_replacement_cost, 1);
      expect(result.breakdown.nominal_costs.financing_cost).toBeCloseTo(expected.breakdown.nominal_costs.financing_cost, 1);
      expect(result.breakdown.npv_costs.carbon_cost).toBeCloseTo(expected.breakdown.npv_costs.carbon_cost, 1);
      expect(result.breakdown.npv_costs.charging_labour_cost).toBeCloseTo(expected.breakdown.npv_costs.charging_labour_cost, 1);
      expect(result.breakdown.npv_costs.payload_penalty_cost).toBeCloseTo(expected.breakdown.npv_costs.payload_penalty_cost, 1);
      expect(result.breakdown.npv_costs.residual_value).toBeCloseTo(expected.breakdown.npv_costs.residual_value, 1);
      expect(result.breakdown.nominal_costs.depreciation).toBeCloseTo(expected.breakdown.nominal_costs.depreciation, 1);
      expect(result.breakdown.upfront_costs.taxes_and_fees).toBeCloseTo(expected.breakdown.upfront_costs.taxes_and_fees, 1);
    });
  });
});
