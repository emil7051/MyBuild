import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency, formatCurrencyCompact, formatPerKilometre } from '@utils/format';

const ComparisonHighlights = () => {
  const results = useTCOStore((state) => state.results);
  const baselineId = useTCOStore((state) => state.wizardData.currentVehicle);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return null;
  }

  const sorted = [...results].sort((a, b) => a.total_cost - b.total_cost);
  const leader = sorted[0];
  const runnerUp = sorted.length > 1 ? sorted[1] : undefined;
  const baselineResult = baselineId
    ? results.find((result) => result.vehicle_id === baselineId)
    : undefined;
  const baseline = baselineResult ?? leader;

  const baselineIsLeader = baseline.vehicle_id === leader.vehicle_id;
  const lifetimeDelta = baselineIsLeader ? 0 : baseline.total_cost - leader.total_cost;
  const annualDelta = baselineIsLeader ? 0 : baseline.annual_cost - leader.annual_cost;
  const runnerDelta = runnerUp ? runnerUp.total_cost - leader.total_cost : undefined;

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
            {formatPerKilometre(leader.cost_per_km)} · {leader.scenario_name}
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
