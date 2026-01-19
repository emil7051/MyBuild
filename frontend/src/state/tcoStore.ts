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
  latestRequestId: number;
  updateWizard: (data: Partial<WizardData>) => void;
  setStepIndex: (index: number) => void;
  setResults: (
    results: CalculationResponsePayload[],
    requestId: number,
    vehicleOrder: string[]
  ) => void;
  resetResults: () => void;
  setIsCalculating: (state: boolean) => void;
  setSessionId: (sessionId?: string) => void;
  getNextRequestId: () => number;
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
  const store = new Map<string, string>();
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
  if (typeof window !== 'undefined' && window.localStorage) {
    const storage = window.localStorage;

    if (
      typeof storage.getItem === 'function' &&
      typeof storage.setItem === 'function' &&
      typeof storage.removeItem === 'function'
    ) {
      return storage;
    }
  }

  return memoryStorage;
};

/**
 * Validates duty cycle values, returning defaults or clamped values if invalid.
 * Checks for NaN, negative values, and totals that don't sum to ~100.
 */
const validateDutyCycle = (dutyCycle?: DutyCycle): DutyCycle | undefined => {
  if (!dutyCycle) return undefined;

  const { urban, regional, longHaul } = dutyCycle;

  // Check for NaN or non-numeric values
  if ([urban, regional, longHaul].some(v => typeof v !== 'number' || isNaN(v))) {
    console.warn('Invalid duty cycle values detected, using defaults');
    return defaultWizardData.dutyCycle;
  }

  // Check for negative values - reset to defaults if any are negative
  if ([urban, regional, longHaul].some(v => v < 0)) {
    console.warn('Negative duty cycle values detected, using defaults');
    return defaultWizardData.dutyCycle;
  }

  // Check if sum is approximately 100 (allow small floating point tolerance)
  const sum = urban + regional + longHaul;
  const tolerance = 0.01;
  if (Math.abs(sum - 100) > tolerance) {
    // If sum is 0, return defaults
    if (sum === 0) {
      console.warn('Duty cycle sum is 0, using defaults');
      return defaultWizardData.dutyCycle;
    }
    // Otherwise normalize to 100
    console.warn(`Duty cycle sum is ${sum}, normalizing to 100`);
    const scale = 100 / sum;
    return {
      urban: Math.round(urban * scale * 100) / 100,
      regional: Math.round(regional * scale * 100) / 100,
      longHaul: Math.round(longHaul * scale * 100) / 100,
    };
  }

  return dutyCycle;
};

export const useTCOStore = create<TCOStore>()(
  persist(
    (set, get) => ({
      stepIndex: 0,
      wizardData: defaultWizardData,
      results: [],
      isCalculating: false,
      vehicleDetails: initialVehicleDetails,
      sessionId: undefined,
      latestRequestId: 0,
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
      getNextRequestId: () => {
        const nextId = get().latestRequestId + 1;
        set({ latestRequestId: nextId });
        return nextId;
      },
      setResults: (results, requestId, vehicleOrder) =>
        set((state) => {
          // Only apply results if this is the latest request
          if (requestId !== state.latestRequestId) {
            return {};
          }
          // Order results based on the captured vehicle order from when the request was made
          const prioritized = vehicleOrder
            .map((vehicleId) => results.find((result) => result.vehicle_id === vehicleId))
            .filter(Boolean) as CalculationResponsePayload[];
          const remainder = results.filter(
            (result) => !vehicleOrder.includes(result.vehicle_id)
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

          // Clear vehicle param overrides for vehicles that no longer exist
          if (state.wizardData.vehicleParamOverrides) {
            const validVehicleIds = new Set(Object.keys(VEHICLE_BY_ID));
            const overrideKeys = Object.keys(state.wizardData.vehicleParamOverrides);
            const invalidKeys = overrideKeys.filter((id) => !validVehicleIds.has(id));

            if (invalidKeys.length > 0) {
              console.info(
                `Clearing stale vehicle overrides for removed vehicles: ${invalidKeys.join(', ')}`
              );
              const validOverrides = { ...state.wizardData.vehicleParamOverrides };
              for (const key of invalidKeys) {
                delete validOverrides[key];
              }
              state.wizardData.vehicleParamOverrides = validOverrides;
            }
          }

          // Clear selected vehicles that no longer exist
          const validVehicleIds = new Set(Object.keys(VEHICLE_BY_ID));
          if (state.wizardData.currentVehicle && !validVehicleIds.has(state.wizardData.currentVehicle)) {
            console.info(`Clearing stale current vehicle: ${state.wizardData.currentVehicle}`);
            state.wizardData.currentVehicle = undefined;
          }
          if (state.wizardData.comparisonVehicles) {
            const validComparisons = state.wizardData.comparisonVehicles.filter((id) =>
              validVehicleIds.has(id)
            );
            if (validComparisons.length !== state.wizardData.comparisonVehicles.length) {
              console.info('Clearing stale comparison vehicles');
              state.wizardData.comparisonVehicles = validComparisons;
            }
          }

          // Clear stale results
          if (state.results && state.results.length > 0) {
            console.info('Clearing stale calculation results due to catalog update');
            state.results = [];
          }
        }

        // Validate duty cycle values (checks for NaN, negative values, and sum != 100)
        const validatedDutyCycle = validateDutyCycle(state.wizardData.dutyCycle);
        if (validatedDutyCycle !== state.wizardData.dutyCycle) {
          state.wizardData.dutyCycle = validatedDutyCycle ?? defaultWizardData.dutyCycle;
        }
      },
    }
  )
);
