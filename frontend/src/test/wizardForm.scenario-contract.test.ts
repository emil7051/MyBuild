import { describe, expect, it } from 'vitest';
import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import { scenarioOptions, wizardFormSchema } from '@forms/wizardForm';

describe('Wizard Scenario Contract', () => {
  it('keeps scenario options in sync with generated scenario definitions', () => {
    const definitionKeys = Object.keys(SCENARIO_DEFINITIONS).sort();
    const optionKeys = scenarioOptions.map((option) => option.value).sort();

    expect(optionKeys).toEqual(definitionKeys);
  });

  it('rejects unknown scenario keys during form validation', () => {
    const result = wizardFormSchema.safeParse({
      scenario: 'not-a-valid-scenario',
      purchaseMethod: 'financed',
      dutyCycle: {
        urban: 60,
        regional: 25,
        longHaul: 15,
      },
      overrides: {},
      vehicleParamOverrides: {},
    });

    expect(result.success).toBe(false);
  });
});
