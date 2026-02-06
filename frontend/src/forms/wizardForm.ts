import { z } from 'zod';
import { OVERRIDE_LIMITS } from '@shared/data/constants';
import { getDutyCycleErrorMessage, validateDutyCycle } from '@shared/types/dutyCycle';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import type { DutyCycle, PurchaseMethod, ScenarioKey } from '@shared/types/tco.types';

export interface ScenarioOption {
  value: ScenarioKey;
  label: string;
  description: string;
}

const scenarioKeys = Object.keys(SCENARIO_DEFINITIONS) as ScenarioKey[];
const costLimits = OVERRIDE_LIMITS.cost;
const vehicleLimits = OVERRIDE_LIMITS.vehicle;

export const scenarioOptions: ScenarioOption[] = scenarioKeys.map((key) => {
  const scenario = SCENARIO_DEFINITIONS[key];
  return {
    value: key,
    label: scenario.name,
    description: scenario.description,
  };
});

export const purchaseOptions: { value: PurchaseMethod; label: string }[] = [
  { value: 'financed', label: 'Financed' },
  { value: 'outright', label: 'Outright' },
];

const dutyCycleSchema = z
  .object({
    urban: z
      .number({
        error: 'Urban % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    regional: z
      .number({
        error: 'Regional % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    longHaul: z
      .number({
        error: 'Long-haul % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
  })
  .superRefine((values, ctx) => {
    const validation = validateDutyCycle(values);
    if (!validation.valid) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: getDutyCycleErrorMessage(validation),
        path: ['longHaul'],
      });
    }
  });

const overridesSchema = z.object({
  annual_kms_variation: z
    .number({
      error: 'Annual kilometres must be a number.',
    })
    .min(costLimits.annual_kms_variation.min, 'Minimum 5,000 km per year.')
    .max(costLimits.annual_kms_variation.max, 'Maximum 250,000 km per year.')
    .optional(),
  residual_value_variation: z
    .number({
      error: 'Residual value must be a number.',
    })
    .min(costLimits.residual_value_variation.min, 'Too low — at least 0.5x the base residual.')
    .max(costLimits.residual_value_variation.max, 'Too high — maximum 1.5x the base residual.')
    .optional(),
  maintenance_cost_variation: z
    .number({
      error: 'Maintenance multiplier must be a number.',
    })
    .min(costLimits.maintenance_cost_variation.min, 'Minimum multiplier is 0.5x.')
    .max(costLimits.maintenance_cost_variation.max, 'Maximum multiplier is 1.5x.')
    .optional(),
  fuel_price_variation: z
    .number({
      error: 'Diesel multiplier must be a number.',
    })
    .min(costLimits.fuel_price_variation.min, 'Minimum multiplier is 0.5x.')
    .max(costLimits.fuel_price_variation.max, 'Maximum multiplier is 2.0x.')
    .optional(),
  electricity_price_variation: z
    .number({
      error: 'Electricity multiplier must be a number.',
    })
    .min(costLimits.electricity_price_variation.min, 'Minimum multiplier is 0.5x.')
    .max(costLimits.electricity_price_variation.max, 'Maximum multiplier is 2.0x.')
    .optional(),
  battery_life_variation: z
    .number({
      error: 'Battery life multiplier must be a number.',
    })
    .min(costLimits.battery_life_variation.min, 'Minimum multiplier is 0.5x.')
    .max(costLimits.battery_life_variation.max, 'Maximum multiplier is 1.5x.')
    .optional(),
  charging_efficiency_variation: z
    .number({
      error: 'Charging efficiency multiplier must be a number.',
    })
    .min(costLimits.charging_efficiency_variation.min, 'Minimum multiplier is 0.7x.')
    .max(costLimits.charging_efficiency_variation.max, 'Maximum multiplier is 1.3x.')
    .optional(),
  apply_road_user_charge_bev: z.boolean().optional(),
});

export const vehicleParamOverridesSchema = z.object({
  msrp_override: z
    .number()
    .min(vehicleLimits.msrp_override.min, 'Must be positive')
    .max(vehicleLimits.msrp_override.max, 'Maximum $10M')
    .optional(),
  payload_override: z
    .number()
    .min(vehicleLimits.payload_override.min, 'Must be positive')
    .max(vehicleLimits.payload_override.max, 'Maximum 100t')
    .optional(),
  range_km_override: z
    .number()
    .min(vehicleLimits.range_km_override.min, 'Minimum 50km')
    .max(vehicleLimits.range_km_override.max, 'Maximum 2500km')
    .optional(),
  battery_capacity_kwh_override: z
    .number()
    .min(vehicleLimits.battery_capacity_kwh_override.min, 'Must be positive')
    .max(vehicleLimits.battery_capacity_kwh_override.max, 'Maximum 2000kWh')
    .optional(),
  kwh_per_km_override: z
    .number()
    .min(vehicleLimits.kwh_per_km_override.min, 'Minimum 0.1 kWh/km')
    .max(vehicleLimits.kwh_per_km_override.max, 'Maximum 10 kWh/km')
    .optional(),
  litres_per_km_override: z
    .number()
    .min(vehicleLimits.litres_per_km_override.min, 'Minimum 0.05 L/km')
    .max(vehicleLimits.litres_per_km_override.max, 'Maximum 5 L/km')
    .optional(),
  annual_registration_override: z
    .number()
    .min(vehicleLimits.annual_registration_override.min, 'Must be positive')
    .max(vehicleLimits.annual_registration_override.max, 'Maximum $100k')
    .optional(),
  interest_rate_override: z
    .number()
    .min(vehicleLimits.interest_rate_override.min, 'Must be positive')
    .max(vehicleLimits.interest_rate_override.max, 'Maximum 20%')
    .optional(),
  charging_time_hours_override: z
    .number()
    .min(vehicleLimits.charging_time_hours_override.min, 'Minimum 0.1 hours')
    .max(vehicleLimits.charging_time_hours_override.max, 'Maximum 8h')
    .optional(),
});

export type VehicleParamOverridesValidated = z.infer<typeof vehicleParamOverridesSchema>;

export const wizardFormSchema = z.object({
  scenario: z.enum(scenarioKeys as [ScenarioKey, ...ScenarioKey[]]),
  purchaseMethod: z.enum(['financed', 'outright']),
  dutyCycle: dutyCycleSchema.default({
    urban: 60,
    regional: 25,
    longHaul: 15,
  } satisfies DutyCycle),
  overrides: overridesSchema.default({}),
  vehicleParamOverrides: z.record(z.string(), vehicleParamOverridesSchema).default({}),
});

export type WizardFormInputValues = z.input<typeof wizardFormSchema>;
export type WizardFormValues = z.output<typeof wizardFormSchema>;
