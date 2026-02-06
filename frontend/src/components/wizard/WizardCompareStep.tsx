import { useEffect, useMemo } from 'react';
import { debounce } from 'lodash-es';
import ResultsPanel from '@components/results/ResultsPanel';
import ComparisonConfigPanel from './ComparisonConfigPanel';
import SelectedVehiclesSummary from './SelectedVehiclesSummary';
import { useTCOStore } from '@state/tcoStore';
import { useCalculationRunner } from '@hooks/useCalculations';
import type { ComparisonRequestPayload } from '@shared/types/tco.types';
import { buildComparisonPayload } from '@utils/payload';

const WizardCompareStep = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const { runComparison } = useCalculationRunner();

  const payload = useMemo<ComparisonRequestPayload | null>(
    () => buildComparisonPayload(wizardData),
    [wizardData]
  );

  // Stable debounced calculation function - created once, survives re-renders
  const debouncedCalculate = useMemo(
    () =>
      debounce((p: ComparisonRequestPayload) => {
        if (!p.vehicle_ids.length) return;
        void runComparison(p).catch((error) => {
          console.warn('Auto-calculation failed:', error);
        });
      }, 600), // Increased debounce to 600ms for stability
    [runComparison]
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
