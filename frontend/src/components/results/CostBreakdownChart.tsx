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

const CostBreakdownChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Cost components"
        subtitle="Stacked view of lifetime cost components for each vehicle."
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
      subtitle="Stacked view of lifetime cost components for each vehicle."
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
