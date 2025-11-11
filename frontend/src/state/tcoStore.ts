import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { VEHICLE_BY_ID } from '@shared/data/vehicleCatalog';
import type {
  CalculationResponsePayload,
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
        set((state) => ({
          wizardData: { ...state.wizardData, ...data },
        })),
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
      partialize: (state) => ({
        wizardData: state.wizardData,
        results: state.results,
        vehicleDetails: state.vehicleDetails,
        sessionId: state.sessionId,
      }),
    }
  )
);
