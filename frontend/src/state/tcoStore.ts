/**
 * @file TCO Store - Application State Management
 * @module frontend/state/tcoStore
 *
 * Zustand store for managing wizard state, calculation results,
 * and session persistence.
 *
 * State is persisted to localStorage under key 'tco-wizard-store'.
 *
 * @see frontend/hooks/useCalculations.ts for calculation triggers
 * @see frontend/pages/WizardPage.tsx for main consumer
 */

import { create } from 'zustand';
import { createJSONStorage, persist, type StateStorage } from 'zustand/middleware';
import { VEHICLE_BY_ID, VEHICLE_CATALOG_VERSION } from '@shared/data/vehicleCatalog';
import type {
  CalculationResponsePayload,
  DutyCycle,
  VehicleDetail,
  WizardData,
} from '@shared/types/tco.types';

interface TCOStore {
  stepIndex: number;
  wizardData: WizardData;
  results: CalculationResponsePayload[];
  isCalculating: boolean;
  vehicleDetails: Record<string, VehicleDetail>;
  sessionId?: string;
  updateWizard: (data: Partial<WizardData>) => void;
  setStepIndex: (index: number) => void;
  setResults: (results: CalculationResponsePayload[]) => void;
  resetResults: () => void;
  setIsCalculating: (state: boolean) => void;
  setSessionId: (sessionId?: string) => void;
}

const defaultWizardData: WizardData = {
  currentVehicle: undefined,
  comparisonVehicles: [],
  scenario: 'baseline',
  purchaseMethod: 'financed',
  dutyCycle: {
    urban: 60,
    regional: 25,
    longHaul: 15,
  },
  overrides: {},
  vehicleParamOverrides: {},
};

const initialVehicleDetails: Record<string, VehicleDetail> = { ...VEHICLE_BY_ID };

const memoryStorage = (() => {
  let store = new Map<string, string>();
  return {
    getItem: (name: string) => (store.has(name) ? store.get(name)! : null),
    setItem: (name: string, value: string) => {
      store.set(name, value);
    },
    removeItem: (name: string) => {
      store.delete(name);
    },
  };
})();

const getPersistStorage = (): StateStorage => {
  const storage = typeof localStorage === 'undefined' ? undefined : localStorage;

  if (
    storage &&
    typeof storage.getItem === 'function' &&
    typeof storage.setItem === 'function' &&
    typeof storage.removeItem === 'function'
  ) {
    return storage;
  }

  return memoryStorage;
};

/**
 * Validates duty cycle values, returning defaults or clamped values if invalid
 */
const validateDutyCycle = (dutyCycle?: DutyCycle): DutyCycle | undefined => {
  if (!dutyCycle) return undefined;

  const { urban, regional, longHaul } = dutyCycle;

  // Check for NaN or non-numeric values
  if ([urban, regional, longHaul].some(v => typeof v !== 'number' || isNaN(v))) {
    console.warn('Invalid duty cycle values detected, using defaults');
    return defaultWizardData.dutyCycle;
  }

  // Check for negative values
  if ([urban, regional, longHaul].some(v => v < 0)) {
    console.warn('Negative duty cycle values detected, clamping to 0');
    return {
      urban: Math.max(0, urban),
      regional: Math.max(0, regional),
      longHaul: Math.max(0, longHaul),
    };
  }

  return dutyCycle;
};

export const useTCOStore = create<TCOStore>()(
  persist(
    (set) => ({
      stepIndex: 0,
      wizardData: defaultWizardData,
      results: [],
      isCalculating: false,
      vehicleDetails: initialVehicleDetails,
      sessionId: undefined,
      updateWizard: (data) =>
        set((state) => {
          const validatedData = { ...data };

          if (data.dutyCycle) {
            validatedData.dutyCycle = validateDutyCycle(data.dutyCycle);
          }

          return {
            wizardData: { ...state.wizardData, ...validatedData },
          };
        }),
      setStepIndex: (index) => set({ stepIndex: index }),
      setResults: (results) =>
        set((state) => {
          const orderedIds = [
            state.wizardData.currentVehicle,
            ...state.wizardData.comparisonVehicles,
          ].filter(Boolean) as string[];
          const prioritized = orderedIds
            .map((vehicleId) => results.find((result) => result.vehicle_id === vehicleId))
            .filter(Boolean) as CalculationResponsePayload[];
          const remainder = results.filter(
            (result) => !orderedIds.includes(result.vehicle_id)
          );
          return { results: [...prioritized, ...remainder] };
        }),
      resetResults: () => set({ results: [] }),
      setIsCalculating: (state) => set({ isCalculating: state }),
      setSessionId: (sessionId) => set({ sessionId }),
    }),
    {
      name: 'tco-wizard-store',
      storage: createJSONStorage(getPersistStorage),
      partialize: (state) => ({
        _vehicleCatalogVersion: VEHICLE_CATALOG_VERSION,
        wizardData: state.wizardData,
        results: state.results,
        vehicleDetails: state.vehicleDetails,
        sessionId: state.sessionId,
      }),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.warn('Failed to rehydrate store:', error);
          return;
        }

        if (!state) return;

        // Check vehicle catalog version and refresh if outdated
        const storedVersion = (state as { _vehicleCatalogVersion?: string })._vehicleCatalogVersion;
        if (storedVersion !== VEHICLE_CATALOG_VERSION) {
          console.info('Vehicle catalog updated, refreshing cache');
          state.vehicleDetails = { ...VEHICLE_BY_ID };
        }

        // Validate duty cycle values
        if (state.wizardData.dutyCycle) {
          const { urban, regional, longHaul } = state.wizardData.dutyCycle;
          const hasInvalidDutyCycle =
            typeof urban !== 'number' || isNaN(urban) ||
            typeof regional !== 'number' || isNaN(regional) ||
            typeof longHaul !== 'number' || isNaN(longHaul);
          if (hasInvalidDutyCycle) {
            state.wizardData.dutyCycle = defaultWizardData.dutyCycle;
          }
        }
      },
    }
  )
);
