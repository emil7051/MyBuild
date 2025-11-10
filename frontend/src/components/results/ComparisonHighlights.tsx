import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency, formatCurrencyCompact, formatPerKilometre } from '@utils/format';

const ComparisonHighlights = () => {
  const results = useTCOStore((state) => state.results);
  const baselineId = useTCOStore((state) => state.wizardData.currentVehicle);

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

  return (
    <Card title="Highlights" subtitle="Key takeaways from the latest comparison run.">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Best option
          </p>
          <p className="text-xl font-semibold text-slate-900">{leader.vehicle_id}</p>
          <p className="text-sm text-slate-500">
            {formatPerKilometre(leader.cost_per_km)} · {leader.scenario_name}
          </p>
          <p className="text-xs text-slate-500">
            Lifetime PV {formatCurrencyCompact(leader.total_cost)}
          </p>
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {baselineIsLeader ? 'Baseline is optimal' : 'Delta vs baseline'}
          </p>
          <p className="text-xl font-semibold text-slate-900">
            {baselineIsLeader ? '—' : formatCurrency(Math.abs(lifetimeDelta))}
          </p>
          <p className="text-sm text-slate-500">
            {baselineIsLeader
              ? 'Your current truck already leads this scenario.'
              : `${lifetimeDelta >= 0 ? 'Savings' : 'Additional cost'} compared to ${
                  baseline.vehicle_id
                }.`}
          </p>
          {!baselineIsLeader && (
            <p className="text-xs text-slate-500">
              Annual delta {formatCurrency(Math.abs(annualDelta))}{' '}
              {annualDelta >= 0 ? 'saved each year.' : 'extra each year.'}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {runnerUp ? 'Gap to next best' : 'Add another vehicle'}
          </p>
          <p className="text-xl font-semibold text-slate-900">
            {runnerUp && runnerDelta !== undefined ? formatCurrency(Math.abs(runnerDelta)) : '—'}
          </p>
          <p className="text-sm text-slate-500">
            {runnerUp
              ? `${runnerUp.vehicle_id} is ${
                  (runnerDelta ?? 0) >= 0 ? 'higher' : 'lower'
                } over the horizon.`
              : 'Select at least one comparator to quantify the gap.'}
          </p>
        </div>
      </div>
    </Card>
  );
};

export default ComparisonHighlights;
