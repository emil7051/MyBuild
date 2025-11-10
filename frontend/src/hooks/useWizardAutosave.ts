import { useEffect, useRef } from 'react';
import { useTCOStore } from '@state/tcoStore';
import { updateSession } from '@services/api';
import type { WizardData } from '@shared/types/tco.types';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';

const sanitizeWizardData = (wizardData: WizardData): WizardData => {
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

export const useWizardAutosave = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const lastSnapshot = useRef<string>('');

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const payload = sanitizeWizardData(wizardData);
    const serialized = JSON.stringify(payload);
    if (serialized === lastSnapshot.current) {
      return;
    }

    const timer = setTimeout(() => {
      lastSnapshot.current = serialized;
      updateSession(sessionId, { wizardData: payload }).catch((error) => {
        console.warn('Autosave failed', error);
      });
    }, 800);

    return () => clearTimeout(timer);
  }, [sessionId, wizardData]);
};
