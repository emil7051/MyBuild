import type { CalculationResponsePayload, VehicleDetail } from '@shared/types/tco.types';

export type ComparisonPairSelectionPolicy = 'first-bev-by-result-order';
export type ComparisonHighlightsSelectionPolicy = 'overall-lowest-total-cost';

export const COMPARISON_PAIR_POLICY: ComparisonPairSelectionPolicy = 'first-bev-by-result-order';
export const COMPARISON_HIGHLIGHTS_POLICY: ComparisonHighlightsSelectionPolicy =
  'overall-lowest-total-cost';

interface ComparisonPairSelection {
  dieselResult: CalculationResponsePayload;
  bevResult: CalculationResponsePayload;
  policy: ComparisonPairSelectionPolicy;
}

interface ComparisonHighlightsSelection {
  leader: CalculationResponsePayload;
  runnerUp?: CalculationResponsePayload;
  policy: ComparisonHighlightsSelectionPolicy;
}

export const selectComparisonPair = (
  results: CalculationResponsePayload[],
  vehicleDetails: Record<string, VehicleDetail>
): ComparisonPairSelection | undefined => {
  const dieselResult = results.find(
    (result) => vehicleDetails[result.vehicle_id]?.drivetrain_type === 'Diesel'
  );
  const bevResult = results.find(
    (result) => vehicleDetails[result.vehicle_id]?.drivetrain_type === 'BEV'
  );

  if (!dieselResult || !bevResult) {
    return undefined;
  }

  return {
    dieselResult,
    bevResult,
    policy: COMPARISON_PAIR_POLICY,
  };
};

export const selectComparisonHighlights = (
  results: CalculationResponsePayload[]
): ComparisonHighlightsSelection | undefined => {
  if (!results.length) {
    return undefined;
  }

  const sortedByTotalCost = [...results].sort((a, b) => a.total_cost - b.total_cost);

  return {
    leader: sortedByTotalCost[0],
    runnerUp: sortedByTotalCost[1],
    policy: COMPARISON_HIGHLIGHTS_POLICY,
  };
};
