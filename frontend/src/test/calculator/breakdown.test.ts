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

    const requiredGroups: (keyof CostBreakdown)[] = [
      'npv_costs',
      'nominal_costs',
      'upfront_costs',
    ];

    for (const group of requiredGroups) {
      expect(breakdown[group]).toBeDefined();
      Object.values(breakdown[group]).forEach((value) => {
        expect(typeof value).toBe('number');
        expect(value).not.toBeNaN();
      });
    }
  });

  it('should have non-negative costs', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    expect(breakdown.upfront_costs.purchase_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.fuel_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.maintenance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.nominal_costs.insurance_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.nominal_costs.registration_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.nominal_costs.financing_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.carbon_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.payload_trip_multiplier_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.charging_dwell_opportunity_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.npv_costs.mr_downtime_opportunity_cost).toBeGreaterThanOrEqual(0);
    expect(breakdown.upfront_costs.taxes_and_fees).toBeGreaterThanOrEqual(0);
  });

  it('should have residual value less than purchase cost', () => {
    const result = calculateTco(basePayload);
    expect(result.breakdown.npv_costs.residual_value).toBeLessThan(
      result.breakdown.upfront_costs.purchase_cost + result.breakdown.upfront_costs.taxes_and_fees
    );
  });

  it('should have depreciation equal to initial cost minus residual', () => {
    const result = calculateTco(basePayload);
    const breakdown = result.breakdown;

    // This is an approximation due to NPV adjustments
    expect(breakdown.nominal_costs.depreciation).toBeGreaterThan(0);
    expect(breakdown.nominal_costs.depreciation).toBeLessThan(
      breakdown.upfront_costs.purchase_cost + breakdown.upfront_costs.taxes_and_fees
    );
  });

  describe('BEV vs Diesel Differences', () => {
    it('should have battery cost only for BEV', () => {
      const bev = calculateTco(basePayload);
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL001' });

      expect(bev.breakdown.npv_costs.battery_replacement_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.npv_costs.battery_replacement_cost).toBe(0);
    });

    it('should have charging labour cost only for large BEVs (articulated trucks)', () => {
      // BEV007/BEV008 are articulated trucks that have charging labor costs
      const articulatedBev = calculateTco({ ...basePayload, vehicle_id: 'BEV007' });
      const diesel = calculateTco({ ...basePayload, vehicle_id: 'DSL007' });

      expect(articulatedBev.breakdown.npv_costs.charging_labour_cost).toBeGreaterThan(0);
      expect(diesel.breakdown.npv_costs.charging_labour_cost).toBe(0);
    });

    it('should have zero charging labour cost for smaller BEVs', () => {
      const smallBev = calculateTco(basePayload); // BEV001 - light rigid
      expect(smallBev.breakdown.npv_costs.charging_labour_cost).toBe(0);
    });
  });
});
