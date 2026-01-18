import Card from '@components/shared/Card';
import { useAnalyticsSummary } from '@hooks/useAnalyticsSummary';
import { formatCurrency } from '@utils/format';

const AnalyticsSummaryCard = () => {
  const { data, isLoading, isError } = useAnalyticsSummary();

  const metrics = [
    {
      label: 'Total sessions',
      value: data ? data.totalSessions.toLocaleString() : '—',
    },
    {
      label: 'Completed sessions',
      value: data ? data.completedSessions.toLocaleString() : '—',
    },
    {
      label: 'Calculations (24h)',
      value: data ? data.calculationsLast24h.toLocaleString() : '—',
    },
    {
      label: 'BEV win rate',
      value:
        data && data.bevWinRate !== null && data.bevWinRate !== undefined
          ? `${(data.bevWinRate * 100).toFixed(1)}%`
          : '—',
    },
    {
      label: 'Average payback',
      value:
        data && data.averagePaybackYears
          ? `${data.averagePaybackYears.toFixed(1)} yrs`
          : '—',
    },
    {
      label: 'Average BEV cost delta',
      value:
        data && data.averageCostDelta !== null && data.averageCostDelta !== undefined
          ? formatCurrency(data.averageCostDelta)
          : '—',
    },
  ];

  return (
    <Card
      title="Platform telemetry"
      subtitle="Aggregated from the autosaved sessions powering TWU analytics."
    >
      {isLoading && <p className="text-sm text-slate-500">Refreshing analytics…</p>}
      {isError && <p className="text-sm text-rose-500">Analytics unavailable. Please retry later.</p>}
      {data && (
        <div className="grid gap-4 md:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="border border-slate-200 p-4 bg-slate-50">
              <p className="text-xs font-bold text-slate-500 mb-1">{metric.label}</p>
              <p className="text-xl font-heading font-bold text-black">{metric.value}</p>
            </div>
          ))}
        </div>
      )}
      {data && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <p className="text-xs font-bold text-slate-500 mb-3">Top vehicles</p>
          {Object.keys(data.topVehicles).length === 0 ? (
            <p className="text-sm text-slate-500">No runs yet.</p>
          ) : (
            <ul className="grid gap-y-2 text-sm text-slate-800">
              {Object.entries(data.topVehicles).map(([vehicleId, count]) => (
                <li key={vehicleId} className="flex justify-between items-center bg-white p-2 border border-slate-100">
                  <span className="font-bold">{vehicleId}</span>
                  <span className="text-xs bg-brand-primary text-black font-bold px-2 py-0.5 rounded-full">{count} runs</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
};

export default AnalyticsSummaryCard;
