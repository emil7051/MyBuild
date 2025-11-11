import Card from '@components/shared/Card';
import ComparisonHighlights from '@components/results/ComparisonHighlights';
import CostBreakdownChart from '@components/results/CostBreakdownChart';
import CostPerKmChart from '@components/results/CostPerKmChart';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const ResultsPanel = () => {
  const results = useTCOStore((state) => state.results);

  if (!results.length) {
    return (
      <Card
        title="No results yet"
        subtitle="Complete the wizard and run a comparison to see the cost breakdown."
      >
        <p className="text-sm text-slate-500">
          Once calculations run, we will show per-vehicle summaries, cost-per-km, and component level
          breakdowns here.
        </p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {results.map((result) => (
          <Card
            key={result.vehicle_id}
            title={`${result.vehicle_id} – ${result.scenario_name}`}
            subtitle="Cost per kilometre"
          >
            <p className="text-3xl font-semibold text-brand-700">
              {new Intl.NumberFormat('en-AU', {
                style: 'currency',
                currency: 'AUD',
                minimumFractionDigits: 2,
              }).format(result.cost_per_km)}
              <span className="text-base font-normal text-slate-500"> / km</span>
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Annual: {formatCurrency(result.annual_cost)} | Lifetime PV: {formatCurrency(result.total_cost)}
            </p>
          </Card>
        ))}
      </div>

      <ComparisonHighlights />

      <div className="grid gap-6 lg:grid-cols-2">
        <CostPerKmChart />
        <CostBreakdownChart />
      </div>
    </div>
  );
};

export default ResultsPanel;
