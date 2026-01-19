import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import type { CalculationResponsePayload } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

// Brand-aligned cost colors
const COST_COLORS = {
  purchase_cost: '#3040B9',
  fuel_cost: '#3B52FF',
  maintenance_cost: '#7080FF',
  insurance_cost: '#B9C2FF',
  registration_cost: '#844A34',
  battery_replacement_cost: '#005A46',
  financing_cost: '#EA5300',
  carbon_cost: '#F2AE95',
  charging_labour_cost: '#00FFC7',
  payload_penalty_cost: '#C5FFF3',
  taxes_and_fees: '#000000',
} as const;

const breakdownSeries = [
  { key: 'purchase_cost', label: 'Purchase', color: COST_COLORS.purchase_cost },
  { key: 'fuel_cost', label: 'Fuel / Energy', color: COST_COLORS.fuel_cost },
  { key: 'maintenance_cost', label: 'Maintenance', color: COST_COLORS.maintenance_cost },
  { key: 'insurance_cost', label: 'Insurance', color: COST_COLORS.insurance_cost },
  { key: 'registration_cost', label: 'Registration', color: COST_COLORS.registration_cost },
  { key: 'battery_replacement_cost', label: 'Battery replacement', color: COST_COLORS.battery_replacement_cost },
  { key: 'financing_cost', label: 'Financing', color: COST_COLORS.financing_cost },
  { key: 'carbon_cost', label: 'Carbon', color: COST_COLORS.carbon_cost },
  { key: 'charging_labour_cost', label: 'Charging labour', color: COST_COLORS.charging_labour_cost },
  { key: 'payload_penalty_cost', label: 'Payload penalty', color: COST_COLORS.payload_penalty_cost },
  { key: 'taxes_and_fees', label: 'Taxes & fees', color: COST_COLORS.taxes_and_fees },
] as const;

type BreakdownKey = keyof CalculationResponsePayload['breakdown'];

// Info tooltip explaining mixed value bases in the breakdown chart
const MixedBasesInfo = () => (
  <span className="inline-flex items-center gap-1">
    Stacked view of lifetime cost components for each vehicle.
    <span className="group relative cursor-help">
      <svg
        className="h-4 w-4 text-slate-400 hover:text-slate-600 transition-colors"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span className="invisible group-hover:visible absolute left-1/2 -translate-x-1/2 top-6 z-10 w-72 rounded-md bg-slate-800 px-3 py-2 text-xs text-white shadow-lg">
        <span className="font-semibold block mb-1">Values have mixed bases:</span>
        <span className="block mb-1">
          <span className="text-emerald-300">NPV-adjusted:</span> Fuel, Maintenance, Battery replacement, Carbon, Charging labour, Payload penalty, Residual value
        </span>
        <span className="block mb-1">
          <span className="text-amber-300">Nominal lifetime:</span> Insurance, Registration, Depreciation
        </span>
        <span className="block">
          <span className="text-sky-300">Upfront:</span> Purchase, Taxes &amp; fees
        </span>
        <span className="absolute -top-1 left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800" />
      </span>
    </span>
  </span>
);

const CostBreakdownChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Cost components"
        subtitle={<MixedBasesInfo />}
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  const data = results.map((result) => {
    const entry: Record<string, number | string> = {
      vehicle: vehicleDetails[result.vehicle_id]?.model_name ?? result.vehicle_id,
    };

    breakdownSeries.forEach(({ key }) => {
      const breakdownValue = result.breakdown[key as BreakdownKey] ?? 0;
      entry[key] = breakdownValue;
    });

    return entry;
  });

  return (
    <Card
      title="Cost components"
      subtitle={<MixedBasesInfo />}
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12, fill: '#000000' }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, { maximumFractionDigits: 0 })
            }
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip
            formatter={(value, name) => {
              const series = breakdownSeries.find((item) => item.key === name);
              return [formatCurrency(value as number), series?.label ?? (name as string)];
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {breakdownSeries.map((series) => (
            <Bar
              key={series.key}
              dataKey={series.key}
              name={series.label}
              stackId="cost"
              fill={series.color}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostBreakdownChart;
