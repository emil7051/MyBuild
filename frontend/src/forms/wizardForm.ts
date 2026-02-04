import { z } from 'zod';
import { DUTY_CYCLE_TOTAL_TOLERANCE } from '@shared/data/constants';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import type { DutyCycle, PurchaseMethod, ScenarioKey } from '@shared/types/tco.types';

export interface ScenarioOption {
  value: ScenarioKey;
  label: string;
  description: string;
}

const scenarioKeys = Object.keys(SCENARIO_DEFINITIONS) as ScenarioKey[];

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
        invalid_type_error: 'Urban % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    regional: z
      .number({
        invalid_type_error: 'Regional % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
    longHaul: z
      .number({
        invalid_type_error: 'Long-haul % must be a number.',
      })
      .min(0, 'Cannot be negative.')
      .max(100, 'Cannot exceed 100%.'),
  })
  .superRefine((values, ctx) => {
    const total = values.urban + values.regional + values.longHaul;
    if (Math.abs(total - 100) > DUTY_CYCLE_TOTAL_TOLERANCE) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Duty cycle must add up to 100%.',
        path: ['longHaul'],
      });
    }
  });

const overridesSchema = z.object({
  annual_kms_variation: z
    .number({
      invalid_type_error: 'Annual kilometres must be a number.',
    })
    .min(5000, 'Minimum 5,000 km per year.')
    .max(250000, 'Maximum 250,000 km per year.')
    .optional(),
  residual_value_variation: z
    .number({
      invalid_type_error: 'Residual value must be a number.',
    })
    .min(0.5, 'Too low — at least 0.5x the base residual.')
    .max(1.5, 'Too high — maximum 1.5x the base residual.')
    .optional(),
  maintenance_cost_variation: z
    .number({
      invalid_type_error: 'Maintenance multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(1.5, 'Maximum multiplier is 1.5x.')
    .optional(),
  fuel_price_variation: z
    .number({
      invalid_type_error: 'Diesel multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(2.0, 'Maximum multiplier is 2.0x.')
    .optional(),
  electricity_price_variation: z
    .number({
      invalid_type_error: 'Electricity multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(2.0, 'Maximum multiplier is 2.0x.')
    .optional(),
  battery_life_variation: z
    .number({
      invalid_type_error: 'Battery life multiplier must be a number.',
    })
    .min(0.5, 'Minimum multiplier is 0.5x.')
    .max(1.5, 'Maximum multiplier is 1.5x.')
    .optional(),
  charging_efficiency_variation: z
    .number({
      invalid_type_error: 'Charging efficiency multiplier must be a number.',
    })
    .min(0.7, 'Minimum multiplier is 0.7x.')
    .max(1.3, 'Maximum multiplier is 1.3x.')
    .optional(),
});

export const vehicleParamOverridesSchema = z.object({
  msrp_override: z.number().min(0, 'Must be positive').max(10_000_000, 'Maximum $10M').optional(),
  payload_override: z.number().min(0, 'Must be positive').max(100, 'Maximum 100t').optional(),
  range_km_override: z.number().min(50, 'Minimum 50km').max(2000, 'Maximum 2000km').optional(),
  battery_capacity_kwh_override: z.number().min(0, 'Must be positive').max(2000, 'Maximum 2000kWh').optional(),
  kwh_per_km_override: z.number().min(0.1, 'Minimum 0.1 kWh/km').max(10, 'Maximum 10 kWh/km').optional(),
  litres_per_km_override: z.number().min(0.05, 'Minimum 0.05 L/km').max(5, 'Maximum 5 L/km').optional(),
  annual_registration_override: z.number().min(0, 'Must be positive').max(100_000, 'Maximum $100k').optional(),
  interest_rate_override: z.number().min(0, 'Must be positive').max(1, 'Maximum 100%').optional(),
  charging_time_hours_override: z.number().min(0.1, 'Minimum 0.1 hours').max(24, 'Maximum 24h').optional(),
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
});

export type WizardFormValues = z.infer<typeof wizardFormSchema>;
