import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';

describe('Vehicle Parameter Overrides', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('MSRP Override', () => {
    it('should increase purchase cost with higher MSRP', () => {
      const standard = calculateTco(basePayload);
      const higherMsrp = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 500000 },
      });

      expect(higherMsrp.breakdown.purchase_cost).toBeGreaterThan(
        standard.breakdown.purchase_cost
      );
    });

    it('should affect depreciation proportionally', () => {
      const standard = calculateTco(basePayload);
      const higherMsrp = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 500000 },
      });

      expect(higherMsrp.breakdown.depreciation).toBeGreaterThan(
        standard.breakdown.depreciation
      );
    });
  });

  describe('Range Override', () => {
    it('should affect charging labor cost', () => {
      const standard = calculateTco(basePayload);
      const higherRange = calculateTco({
        ...basePayload,
        vehicle_overrides: { range_km_override: 600 },
      });

      // Higher range = fewer charging sessions = lower labor cost
      expect(higherRange.breakdown.charging_labour_cost).toBeLessThanOrEqual(
        standard.breakdown.charging_labour_cost
      );
    });
  });

  describe('Efficiency Override (kWh/km)', () => {
    it('should affect fuel cost for BEV', () => {
      const standard = calculateTco(basePayload);
      const lessEfficient = calculateTco({
        ...basePayload,
        vehicle_overrides: { kwh_per_km_override: 2.0 }, // Higher = less efficient
      });

      expect(lessEfficient.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });

  describe('Combined Overrides', () => {
    it('should apply multiple overrides correctly', () => {
      const result = calculateTco({
        ...basePayload,
        vehicle_overrides: {
          msrp_override: 400000,
          range_km_override: 500,
          battery_capacity_kwh_override: 400,
        },
      });

      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.breakdown.purchase_cost).toBeGreaterThan(0);
    });
  });
});

describe('Cost Overrides', () => {
  const basePayload: CalculationRequestPayload = {
    vehicle_id: 'BEV001',
    scenario_name: 'baseline',
    purchase_method: 'outright',
    duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
  };

  describe('Annual KMs Override', () => {
    it('should change fuel costs when annual kms varies', () => {
      const standard = calculateTco(basePayload);
      const higherKms = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 150000 }, // Higher annual kms
      });

      // Higher annual kms should increase fuel costs
      expect(higherKms.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });

    it('should accept absolute annual kms value', () => {
      const result = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 50000 },
      });

      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.breakdown.fuel_cost).toBeGreaterThan(0);
    });
  });

  describe('Fuel Price Variation', () => {
    it('should scale diesel costs with fuel price variation', () => {
      const standard = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
      });
      const higherFuel = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        overrides: { fuel_price_variation: 1.5 }, // 50% higher
      });

      expect(higherFuel.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });

  describe('Electricity Price Variation', () => {
    it('should scale BEV costs with electricity price variation', () => {
      const standard = calculateTco(basePayload);
      const higherElectricity = calculateTco({
        ...basePayload,
        overrides: { electricity_price_variation: 1.5 },
      });

      expect(higherElectricity.breakdown.fuel_cost).toBeGreaterThan(
        standard.breakdown.fuel_cost
      );
    });
  });
});
