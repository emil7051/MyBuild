import { useMemo } from 'react';
import Card from '@components/shared/Card';
import type { CalculationResponsePayload, VehicleDetail } from '@shared/types/tco.types';
import { formatCurrency, formatCurrencyCompact, formatPerKilometre } from '@utils/format';
import { getScenarioLabel } from '@utils/scenario';

interface ComparisonHighlightsProps {
  results: CalculationResponsePayload[];
  baselineId?: string;
  vehicleDetails: Record<string, VehicleDetail>;
}

const ComparisonHighlights = ({
  results,
  baselineId,
  vehicleDetails,
}: ComparisonHighlightsProps) => {
  const highlightData = useMemo(() => {
    if (!results.length) {
      return undefined;
    }

    const sorted = [...results].sort((a, b) => a.total_cost - b.total_cost);
    const memoLeader = sorted[0];
    const memoRunnerUp = sorted.length > 1 ? sorted[1] : undefined;
    const baselineResult = baselineId
      ? results.find((result) => result.vehicle_id === baselineId)
      : undefined;
    const memoBaseline = baselineResult ?? memoLeader;
    const memoBaselineIsLeader = memoBaseline.vehicle_id === memoLeader.vehicle_id;
    const memoLifetimeDelta = memoBaselineIsLeader ? 0 : memoBaseline.total_cost - memoLeader.total_cost;
    const memoAnnualDelta = memoBaselineIsLeader ? 0 : memoBaseline.annual_cost - memoLeader.annual_cost;
    const memoRunnerDelta = memoRunnerUp ? memoRunnerUp.total_cost - memoLeader.total_cost : undefined;

    return {
      leader: memoLeader,
      runnerUp: memoRunnerUp,
      baseline: memoBaseline,
      baselineIsLeader: memoBaselineIsLeader,
      lifetimeDelta: memoLifetimeDelta,
      annualDelta: memoAnnualDelta,
      runnerDelta: memoRunnerDelta,
    };
  }, [baselineId, results]);

  if (!highlightData) {
    return null;
  }

  const {
    leader,
    runnerUp,
    baseline,
    baselineIsLeader,
    lifetimeDelta,
    annualDelta,
    runnerDelta,
  } = highlightData;

  const getDisplayName = (vehicleId: string) =>
    vehicleDetails[vehicleId]?.model_name ?? vehicleId;

  const leaderName = getDisplayName(leader.vehicle_id);
  const baselineName = getDisplayName(baseline.vehicle_id);
  const runnerName = runnerUp ? getDisplayName(runnerUp.vehicle_id) : undefined;

  return (
    <Card title="Key findings" subtitle="Key takeaways from the latest comparison.">
      <div className="grid gap-6 md:grid-cols-3">
        <div className="border-4 border-brand-primary bg-white px-6 py-5 relative">
          <div className="absolute top-0 right-0 bg-brand-primary text-black text-xs font-bold px-2 py-1">
            Lowest cost
          </div>
          <p className="text-xs font-bold text-slate-500 mb-1">
            Best option
          </p>
          <p className="text-2xl font-heading font-bold text-black">{leaderName}</p>
          <p className="text-sm font-medium text-slate-800 mt-2">
            {formatPerKilometre(leader.cost_per_km)} · {getScenarioLabel(leader.scenario_name)}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Total cost {formatCurrencyCompact(leader.total_cost)}
          </p>
        </div>

        <div className="border border-slate-200 bg-white px-6 py-5">
          <p className="text-xs font-bold text-slate-500 mb-1">
            {baselineIsLeader ? 'Diesel is still optimal' : 'Savings vs your current truck'}
          </p>
          <p className="text-2xl font-heading font-bold text-black">
            {baselineIsLeader ? '—' : formatCurrency(Math.abs(lifetimeDelta))}
          </p>
          <p className="text-sm text-slate-600 mt-2">
            {baselineIsLeader
              ? 'Your current truck already leads this scenario.'
              : `${lifetimeDelta >= 0 ? 'Savings' : 'Additional cost'} compared to ${baselineName}.`}
          </p>
          {!baselineIsLeader && (
            <p className="text-xs text-slate-500 mt-1">
              Annual delta {formatCurrency(Math.abs(annualDelta))}{' '}
              {annualDelta >= 0 ? 'saved each year.' : 'extra each year.'}
            </p>
          )}
        </div>

        <div className="border border-slate-200 bg-white px-6 py-5">
          <p className="text-xs font-bold text-slate-500 mb-1">
            {runnerUp ? 'Cost gap' : 'Add another vehicle'}
          </p>
          <p className="text-2xl font-heading font-bold text-black">
            {runnerUp && runnerDelta !== undefined ? formatCurrency(Math.abs(runnerDelta)) : '—'}
          </p>
          <p className="text-sm text-slate-600 mt-2">
            {runnerUp
              ? `${runnerName} is ${(runnerDelta ?? 0) >= 0 ? 'higher' : 'lower'
              } over the horizon.`
              : 'Select at least one comparator to quantify the gap.'}
          </p>
        </div>
      </div>
    </Card>
  );
};

export default ComparisonHighlights;
