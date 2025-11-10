import type {
  CalculationResponsePayload,
  CostOverrides,
  SessionCreatePayload,
  VehicleParamOverrides,
  WizardData,
} from '@shared/types/tco.types';

export const compactOverrides = (overrides?: CostOverrides) =>
  Object.fromEntries(
    Object.entries(overrides ?? {}).filter(
      ([, value]) => value !== undefined && value !== null
    ) as [string, number][]
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

export const buildSessionPayload = (
  wizardData: WizardData,
  results: CalculationResponsePayload[]
): SessionCreatePayload => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides
  );
  const serializedWizard: WizardData = {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
    vehicleParamOverrides: Object.keys(vehicleOverrides).length
      ? vehicleOverrides
      : undefined,
  };

  return {
    wizardData: serializedWizard,
    results,
  };
};
