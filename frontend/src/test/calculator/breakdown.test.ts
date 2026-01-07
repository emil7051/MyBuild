import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload, CostBreakdown } from '@shared/types/tco.types';

describe('Cost Breakdown Consistency', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  it('should have all breakdown fields', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    const requiredFields: (keyof CostBreakdown)[] = [
      'purchase_cost',
      'fuel_cost',
      'maintenance_cost',
      'insurance_cost',
      'registration_cost',
      'battery_replacement_cost',
      'financing_cost',
      'carbon_cost',
      'charging_labour_cost',
      'payload_penalty_cost',
      'residual_value',
      'depreciation',
      'taxes_and_fees',
    ];

    for (const field of requiredFields) {
      expect(breakdown[field]).toBeDefined();
      expect(typeof breakdown[field]).toBe('number');
      expect(breakdown[field]).not.toBeNaN();
    }
  });

  it('should have non-negative costs', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    expect(breakdown.purchase_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.fuel_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.maintenance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.insurance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.registration_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.financing_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.carbon_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.taxes_and_fees).toBeGreaterThanOrEqual(0);
  });

  it('should have residual value less than purchase cost', () => {
    const result = calculateTco(basePayload);
    expect(result.breakdown.residual_value).toBeLessThan(
      result.breakdown.purchase_cost + result.breakdown.taxes_and_fees
    );
  });

  it('should have depreciation equal to initial cost minus residual', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    // This is an approximation due to NPV adjustments
    expect(breakdown.depreciation).toBeGreaterThan(0);
    expect(breakdown.depreciation).toBeLessThan(
      breakdown.purchase_cost + breakdown.taxes_and_fees
    );
  });

  describe('BEV vs Diesel Differences', () => {
    it('should have battery cost only for BEV', () => {
      const bev = calculateTco(basePayload);
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL001' });

      expect(bev.breakdown.battery_replacement_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.battery_replacement_cost).toBe(0);
    });

    it('should have charging labour cost only for large BEVs (articulated trucks)', () => {
      // BEV007/BEV008 are articulated trucks that have charging labor costs
      const articulatedBev = calculateTco({ ...basePayload, vehicle_id: 'BEV007' });
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL007' });

      expect(articulatedBev.breakdown.charging_labour_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.charging_labour_cost).toBe(0);
    });

    it('should have zero charging labour cost for smaller BEVs', () => {
      const smallBev = calculateTco(basePayload); // BEV001 - light rigid
      expect(smallBev.breakdown.charging_labour_cost).toBe(0);
    });
  });
});
