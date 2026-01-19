import { useEffect, useMemo, useRef } from 'react';
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

  // Generation counter to prevent stale results from overwriting newer ones
  const generationRef = useRef(0);

  const payload = useMemo<ComparisonRequestPayload | null>(() => {
    if (!wizardData.currentVehicle) {
      return null;
    }
    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles])
    ).filter(Boolean) as string[];
    if (!vehicleIds.length) {
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

  useEffect(() => {
    if (!payload) {
      return;
    }

    const currentGeneration = ++generationRef.current;

    const timer = setTimeout(() => {
      // Skip if payload has no vehicles
      if (!payload.vehicle_ids.length) {
        return;
      }

      setIsCalculating(true);
      try {
        const results = calculateComparison(payload);

        // Only apply results if this is still the latest generation
        if (currentGeneration === generationRef.current) {
          setResults(results);
        }
      } catch (error) {
        console.warn('Preview calculation failed:', error);
      } finally {
        if (currentGeneration === generationRef.current) {
          setIsCalculating(false);
        }
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [payload, setIsCalculating, setResults]);

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
