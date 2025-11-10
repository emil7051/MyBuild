import type {
  CalculationResponsePayload,
  CostOverrides,
  SessionCreatePayload,
  WizardData,
} from '@shared/types/tco.types';

export const compactOverrides = (overrides?: CostOverrides) =>
  Object.fromEntries(
    Object.entries(overrides ?? {}).filter(
      ([, value]) => value !== undefined && value !== null
    ) as [string, number][]
  ) as CostOverrides;

export const buildSessionPayload = (
  wizardData: WizardData,
  results: CalculationResponsePayload[]
): SessionCreatePayload => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const serializedWizard: WizardData = {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
  };

  return {
    wizardData: serializedWizard,
    results,
  };
};
