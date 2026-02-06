import type {
  CalculationResponsePayload,
  ComparisonRequestPayload,
  CostOverrides,
  SessionCreatePayload,
  VehicleParamOverrides,
  WizardData,
} from '@shared/types/tco.types';
import { validateDutyCycle } from '@shared/types/dutyCycle';

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

export const hasValidWizardDutyCycle = (wizardData: WizardData): boolean =>
  validateDutyCycle(wizardData.dutyCycle).valid;

export const buildComparisonPayload = (
  wizardData: WizardData
): ComparisonRequestPayload | null => {
  if (!wizardData.currentVehicle) {
    return null;
  }

  const vehicleIds = Array.from(
    new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles])
  ).filter(Boolean) as string[];

  if (!vehicleIds.length) {
    return null;
  }

  if (!hasValidWizardDutyCycle(wizardData)) {
    return null;
  }

  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides ?? {}
  );

  const payload: ComparisonRequestPayload = {
    vehicle_ids: vehicleIds,
    scenario_name: wizardData.scenario,
    purchase_method: wizardData.purchaseMethod,
    duty_cycle: wizardData.dutyCycle,
  };

  if (Object.keys(overrides).length) {
    payload.overrides = overrides;
  }
  if (Object.keys(vehicleOverrides).length) {
    payload.vehicle_param_overrides = vehicleOverrides;
  }

  return payload;
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
