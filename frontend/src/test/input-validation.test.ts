import { describe, it, expect } from 'vitest';
import { vehicleParamOverridesSchema } from '@forms/wizardForm';

describe('Input Validation', () => {
  describe('vehicleParamOverridesSchema', () => {
    it('should accept valid overrides', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 150000,
        range_km_override: 400,
      });
      expect(result.success).toBe(true);
    });

    it('should accept all valid override fields', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 250000,
        payload_override: 10,
        range_km_override: 500,
        battery_capacity_kwh_override: 300,
        kwh_per_km_override: 1.5,
        litres_per_km_override: 0.3,
        annual_registration_override: 5000,
        interest_rate_override: 0.06,
        charging_time_hours_override: 2,
      });
      expect(result.success).toBe(true);
    });

    it('should reject negative values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: -1000,
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for msrp', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 100_000_000, // Exceeds max of 10M
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for range', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        range_km_override: 3000, // Exceeds max of 2000
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for battery capacity', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        battery_capacity_kwh_override: 5000, // Exceeds max of 2000
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for interest rate', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        interest_rate_override: 1.5, // Exceeds max of 1 (100%)
      });
      expect(result.success).toBe(false);
    });

    it('should reject values exceeding max for charging time', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        charging_time_hours_override: 48, // Exceeds max of 24
      });
      expect(result.success).toBe(false);
    });

    it('should accept empty object', () => {
      const result = vehicleParamOverridesSchema.safeParse({});
      expect(result.success).toBe(true);
    });

    it('should accept undefined values for optional fields', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: undefined,
        range_km_override: undefined,
      });
      expect(result.success).toBe(true);
    });

    it('should accept zero values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: 0,
        interest_rate_override: 0,
      });
      expect(result.success).toBe(true);
    });

    it('should reject NaN values', () => {
      const result = vehicleParamOverridesSchema.safeParse({
        msrp_override: NaN,
      });
      expect(result.success).toBe(false);
    });
  });
});
