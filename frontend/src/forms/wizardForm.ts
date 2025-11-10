import { z } from 'zod';
import type { DutyCycle, PurchaseMethod, ScenarioKey } from '@shared/types/tco.types';

export interface ScenarioOption {
  value: ScenarioKey;
  label: string;
  description: string;
}

export const scenarioOptions: ScenarioOption[] = [
  {
    value: 'baseline',
    label: 'Baseline',
    description: 'Steady 2-3% fuel escalators, moderate maintenance curve, current battery pricing.',
  },
  {
    value: 'technology_breakthrough',
    label: 'Technology breakthrough',
    description: 'Faster battery cost decline, improved BEV efficiency, maintenance advantage extends.',
  },
  {
    value: 'oil_crisis',
    label: 'Oil crisis',
    description: 'Diesel price spike in year 3 and beyond, higher volatility, electricity steady at +3%/yr.',
  },
];

export const purchaseOptions: { value: PurchaseMethod; label: string }[] = [
  { value: 'financed', label: 'Financed (default)' },
  { value: 'outright', label: 'Outright purchase' },
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
    if (Math.round(total) !== 100) {
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

export const wizardFormSchema = z.object({
  scenario: z.enum(['baseline', 'technology_breakthrough', 'oil_crisis']),
  purchaseMethod: z.enum(['financed', 'outright']),
  dutyCycle: dutyCycleSchema.default({
    urban: 60,
    regional: 25,
    longHaul: 15,
  } satisfies DutyCycle),
  overrides: overridesSchema.default({}),
});

export type WizardFormValues = z.infer<typeof wizardFormSchema>;
