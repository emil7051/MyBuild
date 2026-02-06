import { describe, it, expect } from 'vitest';
import { calculateTco } from '@shared/calculator';
import { CONSTANTS } from '@shared/data/constants';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import { VEHICLE_BY_ID } from '@shared/data/vehicleCatalog';
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

      expect(higherMsrp.breakdown.upfront_costs.purchase_cost).toBeGreaterThan(
        standard.breakdown.upfront_costs.purchase_cost
      );
    });

    it('should affect depreciation proportionally', () => {
      const standard = calculateTco(basePayload);
      const higherMsrp = calculateTco({
        ...basePayload,
        vehicle_overrides: { msrp_override: 500000 },
      });

      expect(higherMsrp.breakdown.nominal_costs.depreciation).toBeGreaterThan(
        standard.breakdown.nominal_costs.depreciation
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
      expect(higherRange.breakdown.npv_costs.charging_labour_cost).toBeLessThanOrEqual(
        standard.breakdown.npv_costs.charging_labour_cost
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

      expect(lessEfficient.breakdown.npv_costs.fuel_cost).toBeGreaterThan(
        standard.breakdown.npv_costs.fuel_cost
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
      expect(result.breakdown.upfront_costs.purchase_cost).toBeGreaterThan(0);
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
      expect(higherKms.breakdown.npv_costs.fuel_cost).toBeGreaterThan(
        standard.breakdown.npv_costs.fuel_cost
      );
    });

    it('should accept absolute annual kms value', () => {
      const result = calculateTco({
        ...basePayload,
        overrides: { annual_kms_variation: 50000 },
      });

      expect(result.total_cost).toBeGreaterThan(0);
      expect(result.breakdown.npv_costs.fuel_cost).toBeGreaterThan(0);
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

      expect(higherFuel.breakdown.npv_costs.fuel_cost).toBeGreaterThan(
        standard.breakdown.npv_costs.fuel_cost
      );
    });

    it('should apply fuel tax credit to diesel fuel costs', () => {
      const diesel = VEHICLE_BY_ID.DSL001;
      const scenario = SCENARIO_DEFINITIONS.baseline;
      const vehicleLife = CONSTANTS.VEHICLE_LIFE as number;
      const discountRate = CONSTANTS.DISCOUNT_RATE as number;
      const dieselPrice = CONSTANTS.DIESEL_PRICE as number;
      const fuelTaxCredit = CONSTANTS.FUEL_TAX_CREDIT as number;
      const effectiveDieselPrice = dieselPrice - fuelTaxCredit;

      const expectedFuelCost = Array.from({ length: vehicleLife }, (_, index) => {
        const efficiencyMultiplier = scenario.diesel_efficiency_improvement[index] ?? 1;
        const priceMultiplier = scenario.diesel_price_trajectory[index] ?? 1;
        const annualFuelCost =
          diesel.litres_per_km * efficiencyMultiplier * diesel.annual_kms * effectiveDieselPrice * priceMultiplier;
        return annualFuelCost / (1 + discountRate) ** index;
      }).reduce((sum, value) => sum + value, 0);

      const result = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
      });

      expect(result.breakdown.npv_costs.fuel_cost).toBeCloseTo(expectedFuelCost, 6);
    });
  });

  describe('Electricity Price Variation', () => {
    it('should scale BEV costs with electricity price variation', () => {
      const standard = calculateTco(basePayload);
      const higherElectricity = calculateTco({
        ...basePayload,
        overrides: { electricity_price_variation: 1.5 },
      });

      expect(higherElectricity.breakdown.npv_costs.fuel_cost).toBeGreaterThan(
        standard.breakdown.npv_costs.fuel_cost
      );
    });
  });

  describe('BEV Road User Charge Toggle', () => {
    it('should remain off by default', () => {
      const defaultResult = calculateTco(basePayload);
      const explicitOff = calculateTco({
        ...basePayload,
        overrides: { apply_road_user_charge_bev: false },
      });

      expect(explicitOff.breakdown.npv_costs.fuel_cost).toBeCloseTo(defaultResult.breakdown.npv_costs.fuel_cost, 6);
    });

    it('should increase BEV fuel/energy costs when enabled', () => {
      const defaultResult = calculateTco(basePayload);
      const withRoadUserCharge = calculateTco({
        ...basePayload,
        overrides: { apply_road_user_charge_bev: true },
      });

      expect(withRoadUserCharge.breakdown.npv_costs.fuel_cost).toBeGreaterThan(defaultResult.breakdown.npv_costs.fuel_cost);
    });

    it('should not affect diesel vehicles when enabled', () => {
      const dieselDefault = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
      });
      const dieselWithToggle = calculateTco({
        ...basePayload,
        vehicle_id: 'DSL001',
        overrides: { apply_road_user_charge_bev: true },
      });

      expect(dieselWithToggle.breakdown.npv_costs.fuel_cost).toBeCloseTo(dieselDefault.breakdown.npv_costs.fuel_cost, 6);
    });
  });
});
