import type {
  CalculationResponsePayload,
  CostOverrides,
  SessionCreatePayload,
  VehicleParamOverrides,
  WizardData,
} from '@shared/types/tco.types';

export const compactOverrides = (overrides?: CostOverrides) =>
  Object.fromEntries(
    Object.entries(overrides ?? {}).filter(([, value]) => value !== undefined && value !== null)
  ) as CostOverrides;

export const compactVehicleParamOverrides = (
  overrides?: Record<string, VehicleParamOverrides>
) => {
  const cleaned: Record<string, VehicleParamOverrides> = {};
  Object.entries(overrides ?? {}).forEach(([vehicleId, fields]) => {
    const filteredEntries = Object.entries(fields ?? {}).filter(
      ([, value]) => value !== undefined && value !== null
    );
    if (filteredEntries.length) {
      cleaned[vehicleId] = Object.fromEntries(
        filteredEntries
      ) as VehicleParamOverrides;
    }
  });
  return cleaned;
};

export const sanitizeWizardData = (wizardData: WizardData): WizardData => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides ?? {}
  );

  return {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
    vehicleParamOverrides: Object.keys(vehicleOverrides).length
      ? vehicleOverrides
      : undefined,
  };
};

export const buildSessionPayload = (
  wizardData: WizardData,
  results: CalculationResponsePayload[]
): SessionCreatePayload => {
  const serializedWizard = sanitizeWizardData(wizardData);

  return {
    wizardData: serializedWizard,
    results,
  };
};
