import Card from '@components/shared/Card';
import ComparisonHighlights from '@components/results/ComparisonHighlights';
import CostBreakdownChart from '@components/results/CostBreakdownChart';
import CostPerKmChart from '@components/results/CostPerKmChart';
import type { CalculationResponsePayload } from '@shared/types/tco.types';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const costLabels: Record<string, string> = {
  purchase_cost: 'Purchase',
  fuel_cost: 'Fuel / Energy',
  maintenance_cost: 'Maintenance',
  insurance_cost: 'Insurance',
  registration_cost: 'Registration',
  battery_replacement_cost: 'Battery replacement',
  financing_cost: 'Financing',
  carbon_cost: 'Carbon',
  charging_labour_cost: 'Charging labour',
  payload_penalty_cost: 'Payload penalty',
  residual_value: 'Residual value (PV)',
  depreciation: 'Depreciation',
  taxes_and_fees: 'Taxes & fees',
};

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

      <Card title="Cost breakdown" subtitle="All numbers are present value across the 15-year horizon.">
        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr>
                <th className="py-2 text-left font-semibold text-slate-500">Component</th>
                {results.map((result) => (
                  <th key={result.vehicle_id} className="py-2 text-right font-semibold text-slate-500">
                    {result.vehicle_id}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {Object.entries(costLabels).map(([key, label]) => {
                const breakdownKey = key as keyof CalculationResponsePayload['breakdown'];
                return (
                  <tr key={key}>
                    <td className="py-2 text-slate-600">{label}</td>
                    {results.map((result) => (
                    <td
                      key={`${result.vehicle_id}-${key}`}
                      className="py-2 text-right font-medium text-slate-900"
                    >
                      {formatCurrency(result.breakdown[breakdownKey] ?? 0)}
                    </td>
                  ))}
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ResultsPanel;
