import { describe, it, expect } from 'vitest';
import { buildComparisonPayload, sanitizeWizardData } from '@utils/payload';
import type { VehicleParamOverrides, WizardData } from '@shared/types/tco.types';

describe('sanitizeWizardData', () => {
  const baseWizardData: WizardData = {
    currentVehicle: 'BEV001',
    comparisonVehicles: [],
    scenario: 'baseline',
    purchaseMethod: 'financed',
    dutyCycle: { urban: 60, regional: 25, longHaul: 15 },
    overrides: {},
    vehicleParamOverrides: {},
  };

  it('removes undefined/null overrides and drops empty sections', () => {
    const input: WizardData = {
      ...baseWizardData,
      overrides: {
        fuel_price_variation: undefined,
        electricity_price_variation: 1.1,
      },
      vehicleParamOverrides: {
        BEV001: {
          range_km_override: undefined,
          charging_time_hours_override: 2,
        },
        DSL001: {
          payload_override: undefined,
        } as VehicleParamOverrides,
      },
    };

    const sanitized = sanitizeWizardData(input);

    expect(sanitized.overrides).toEqual({
      electricity_price_variation: 1.1,
    });
    expect(sanitized.vehicleParamOverrides).toEqual({
      BEV001: { charging_time_hours_override: 2 },
    });
  });

  it('returns undefined for overrides and vehicleParamOverrides when empty', () => {
    const input: WizardData = {
      ...baseWizardData,
      overrides: {
        fuel_price_variation: undefined,
      },
      vehicleParamOverrides: {
        BEV001: {
          range_km_override: undefined,
        },
      },
    };

    const sanitized = sanitizeWizardData(input);

    expect(sanitized.overrides).toBeUndefined();
    expect(sanitized.vehicleParamOverrides).toBeUndefined();
  });
});

describe('buildComparisonPayload', () => {
  const baseWizardData: WizardData = {
    currentVehicle: 'DSL001',
    comparisonVehicles: ['BEV001'],
    scenario: 'baseline',
    purchaseMethod: 'financed',
    dutyCycle: { urban: 60, regional: 25, longHaul: 15 },
    overrides: {},
    vehicleParamOverrides: {},
  };

  it('builds a compacted payload and de-duplicates vehicle ids', () => {
    const payload = buildComparisonPayload({
      ...baseWizardData,
      comparisonVehicles: ['BEV001', 'DSL001', 'BEV001', ''],
      overrides: {
        fuel_price_variation: undefined,
        electricity_price_variation: 1.1,
      },
      vehicleParamOverrides: {
        BEV001: {
          range_km_override: undefined,
          charging_time_hours_override: 2,
        },
        DSL001: {
          payload_override: undefined,
        } as VehicleParamOverrides,
      },
    });

    expect(payload).toEqual({
      vehicle_ids: ['DSL001', 'BEV001'],
      scenario_name: 'baseline',
      purchase_method: 'financed',
      duty_cycle: { urban: 60, regional: 25, longHaul: 15 },
      overrides: {
        electricity_price_variation: 1.1,
      },
      vehicle_param_overrides: {
        BEV001: { charging_time_hours_override: 2 },
      },
    });
  });

  it('returns null when no current vehicle is selected', () => {
    const payload = buildComparisonPayload({
      ...baseWizardData,
      currentVehicle: undefined,
    });
    expect(payload).toBeNull();
  });

  it('returns null when duty cycle is invalid', () => {
    const payload = buildComparisonPayload({
      ...baseWizardData,
      dutyCycle: { urban: 40, regional: 40, longHaul: 10 },
    });
    expect(payload).toBeNull();
  });
});
