import { describe, it, expect } from 'vitest';
import { sanitizeWizardData } from '@utils/payload';
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
