import Card from '@components/shared/Card';
import ComparisonHighlights from '@components/results/ComparisonHighlights';
import CostBreakdownChart from '@components/results/CostBreakdownChart';
import CostPerKmChart from '@components/results/CostPerKmChart';
import PaybackChart from '@components/results/PaybackChart';
import SavingsWaterfallChart from '@components/results/SavingsWaterfallChart';
import SensitivityTornadoChart from '@components/results/SensitivityTornadoChart';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const ResultsPanel = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const isCalculating = useTCOStore((state) => state.isCalculating);

  if (isCalculating) {
    return (
      <Card
        title="Calculating..."
        subtitle="Running the comparison analysis."
      >
        <div className="flex h-32 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-brand-primary" />
        </div>
      </Card>
    );
  }

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

  // Check if we have both diesel and BEV for deeper analysis
  const hasDiesel = results.some((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const hasBev = results.some((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');
  const showDeeperAnalysis = hasDiesel && hasBev;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {results.map((result) => {
          const modelName = vehicleDetails[result.vehicle_id]?.model_name ?? result.vehicle_id;
          return (
            <Card
              key={result.vehicle_id}
              title={`${modelName} - ${result.scenario_name}`}
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
                Annual: {formatCurrency(result.annual_cost)} | Total cost:{' '}
                {formatCurrency(result.total_cost)}
              </p>
            </Card>
          );
        })}
      </div>

      <ComparisonHighlights />

      <div className="grid gap-6 lg:grid-cols-2">
        <CostPerKmChart />
        <CostBreakdownChart />
      </div>

      {showDeeperAnalysis && (
        <>
          <div className="mt-4">
            <h2 className="text-xl font-heading font-bold text-black">Deeper Analysis</h2>
            <p className="text-sm text-slate-600 mt-1">
              Explore the financial dynamics of your diesel vs electric comparison.
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <PaybackChart />
            <SavingsWaterfallChart />
          </div>

          <SensitivityTornadoChart />
        </>
      )}
    </div>
  );
};

export default ResultsPanel;
