import { Component, Suspense, lazy, type ErrorInfo, type ReactNode } from 'react';
import Card from '@components/shared/Card';
import { reportClientError } from '@services/clientTelemetry';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';
import { getScenarioLabel } from '@utils/scenario';

const ComparisonHighlights = lazy(() => import('@components/results/ComparisonHighlights'));
const CostBreakdownChart = lazy(() => import('@components/results/CostBreakdownChart'));
const CostPerKmChart = lazy(() => import('@components/results/CostPerKmChart'));
const PaybackChart = lazy(() => import('@components/results/PaybackChart'));
const SavingsWaterfallChart = lazy(() => import('@components/results/SavingsWaterfallChart'));
const SensitivityTornadoChart = lazy(() => import('@components/results/SensitivityTornadoChart'));

interface ChartFallbackProps {
  title: string;
  subtitle: string;
}

const ChartFallback = ({ title, subtitle }: ChartFallbackProps) => (
  <Card title={title} subtitle={subtitle}>
    <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-brand-primary" />
    </div>
  </Card>
);

const ChartErrorFallback = ({ title, subtitle }: ChartFallbackProps) => (
  <Card title={title} subtitle={subtitle}>
    <div className="flex h-64 items-center justify-center rounded-lg border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-700">
      We could not render this chart right now. Other results remain available.
    </div>
  </Card>
);

interface ChartErrorBoundaryProps extends ChartFallbackProps {
  children: ReactNode;
}

interface ChartErrorBoundaryState {
  hasError: boolean;
}

class ChartErrorBoundary extends Component<ChartErrorBoundaryProps, ChartErrorBoundaryState> {
  state: ChartErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): ChartErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    reportClientError({
      source: 'ResultsPanel.ChartErrorBoundary',
      error,
      context: {
        componentStack: errorInfo.componentStack,
        title: this.props.title,
      },
      level: 'warning',
    });
  }

  render() {
    if (this.state.hasError) {
      return <ChartErrorFallback title={this.props.title} subtitle={this.props.subtitle} />;
    }

    return this.props.children;
  }
}

interface ChartSectionProps extends ChartFallbackProps {
  children: ReactNode;
}

const ChartSection = ({ title, subtitle, children }: ChartSectionProps) => (
  <ChartErrorBoundary title={title} subtitle={subtitle}>
    <Suspense fallback={<ChartFallback title={title} subtitle={subtitle} />}>{children}</Suspense>
  </ChartErrorBoundary>
);

const ResultsPanel = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const wizardData = useTCOStore((state) => state.wizardData);
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
              title={`${modelName} - ${getScenarioLabel(result.scenario_name)}`}
              subtitle="Cost per kilometre"
            >
              <p className="text-3xl font-semibold text-brand-700">
                {formatCurrency(result.cost_per_km, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
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

      <ChartSection
        title="Key findings"
        subtitle="Key takeaways from the latest comparison."
      >
        <ComparisonHighlights
          results={results}
          baselineId={wizardData.currentVehicle}
          vehicleDetails={vehicleDetails}
        />
      </ChartSection>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartSection
          title="Cost per kilometre"
          subtitle="Lower bars indicate cheaper ownership under the selected scenario."
        >
          <CostPerKmChart results={results} vehicleDetails={vehicleDetails} />
        </ChartSection>
        <ChartSection
          title="Cost components"
          subtitle="Grouped cost-basis components for each vehicle."
        >
          <CostBreakdownChart results={results} vehicleDetails={vehicleDetails} />
        </ChartSection>
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
            <ChartSection
              title="Payback timeline"
              subtitle="When does switching to electric break even?"
            >
              <PaybackChart
                results={results}
                vehicleDetails={vehicleDetails}
                wizardData={wizardData}
              />
            </ChartSection>
            <ChartSection
              title="Savings breakdown"
              subtitle="What drives the cost difference?"
            >
              <SavingsWaterfallChart results={results} vehicleDetails={vehicleDetails} />
            </ChartSection>
          </div>

          <ChartSection
            title="Sensitivity analysis (approximate)"
            subtitle="How do assumptions affect the comparison?"
          >
            <SensitivityTornadoChart results={results} vehicleDetails={vehicleDetails} />
          </ChartSection>
        </>
      )}
    </div>
  );
};

export default ResultsPanel;
