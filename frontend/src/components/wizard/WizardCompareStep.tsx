import { useEffect, useMemo } from 'react';
import { debounce } from 'lodash-es';
import ResultsPanel from '@components/results/ResultsPanel';
import ComparisonConfigPanel from './ComparisonConfigPanel';
import SelectedVehiclesSummary from './SelectedVehiclesSummary';
import { useTCOStore } from '@state/tcoStore';
import type { ComparisonRequestPayload } from '@shared/types/tco.types';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';
import { calculateComparison } from '@shared/calculator';

const WizardCompareStep = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const getNextRequestId = useTCOStore((state) => state.getNextRequestId);

  const payload = useMemo<ComparisonRequestPayload | null>(() => {
    console.log('[WizardCompareStep] Building payload, dutyCycle:', wizardData.dutyCycle);

    if (!wizardData.currentVehicle) {
      console.log('[WizardCompareStep] No current vehicle, payload = null');
      return null;
    }
    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles])
    ).filter(Boolean) as string[];
    if (!vehicleIds.length) {
      console.log('[WizardCompareStep] No vehicle IDs, payload = null');
      return null;
    }

    const overrides = compactOverrides(wizardData.overrides ?? {});
    const vehicleOverrides = compactVehicleParamOverrides(
      wizardData.vehicleParamOverrides ?? {}
    );

    const request: ComparisonRequestPayload = {
      vehicle_ids: vehicleIds,
      scenario_name: wizardData.scenario,
      purchase_method: wizardData.purchaseMethod,
      duty_cycle: wizardData.dutyCycle,
    };

    if (Object.keys(overrides).length) {
      request.overrides = overrides;
    }
    if (Object.keys(vehicleOverrides).length) {
      request.vehicle_param_overrides = vehicleOverrides;
    }

    console.log('[WizardCompareStep] Payload built:', {
      duty_cycle: request.duty_cycle,
      scenario: request.scenario_name,
    });

    return request;
  }, [
    wizardData.currentVehicle,
    wizardData.comparisonVehicles,
    wizardData.overrides,
    wizardData.purchaseMethod,
    wizardData.scenario,
    wizardData.vehicleParamOverrides,
    wizardData.dutyCycle,
  ]);

  // Stable debounced calculation function - created once, survives re-renders
  const debouncedCalculate = useMemo(
    () =>
      debounce((p: ComparisonRequestPayload) => {
        if (!p.vehicle_ids.length) return;

        const requestId = getNextRequestId();
        const vehicleOrder = p.vehicle_ids;

        console.log('[WizardCompareStep] Auto-calc running with duty_cycle:', p.duty_cycle);

        setIsCalculating(true);
        try {
          const results = calculateComparison(p);
          console.log('[WizardCompareStep] Calculation complete, first result cost_per_km:', results[0]?.cost_per_km);
          setResults(results, requestId, vehicleOrder);
        } catch (error) {
          console.warn('Auto-calculation failed:', error);
        } finally {
          setIsCalculating(false);
        }
      }, 600), // Increased debounce to 600ms for stability
    [getNextRequestId, setIsCalculating, setResults]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      debouncedCalculate.cancel();
    };
  }, [debouncedCalculate]);

  // Trigger calculation when payload changes
  useEffect(() => {
    if (payload) {
      console.log('[WizardCompareStep] Payload changed, scheduling auto-calc');
      debouncedCalculate(payload);
    }
  }, [payload, debouncedCalculate]);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <div className="flex flex-col gap-6">
        <ResultsPanel />
        <SelectedVehiclesSummary />
      </div>
      <ComparisonConfigPanel />
    </div>
  );
};

export default WizardCompareStep;
