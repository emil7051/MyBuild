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

const breakdownSeries = [
  { key: 'purchase_cost', label: 'Purchase', color: '#0f31a1' },
  { key: 'fuel_cost', label: 'Fuel / Energy', color: '#2563eb' },
  { key: 'maintenance_cost', label: 'Maintenance', color: '#38bdf8' },
  { key: 'insurance_cost', label: 'Insurance', color: '#0ea5e9' },
  { key: 'registration_cost', label: 'Registration', color: '#06b6d4' },
  { key: 'battery_replacement_cost', label: 'Battery replacement', color: '#14b8a6' },
  { key: 'financing_cost', label: 'Financing', color: '#f97316' },
  { key: 'carbon_cost', label: 'Carbon', color: '#facc15' },
  { key: 'charging_labour_cost', label: 'Charging labour', color: '#84cc16' },
  { key: 'payload_penalty_cost', label: 'Payload penalty', color: '#a855f7' },
  { key: 'taxes_and_fees', label: 'Taxes & fees', color: '#f43f5e' },
] as const;

type BreakdownKey = keyof CalculationResponsePayload['breakdown'];

const CostBreakdownChart = () => {
  const results = useTCOStore((state) => state.results);

  if (!results.length) {
    return null;
  }

  const data = results.map((result) => {
    const entry: Record<string, number | string> = {
      vehicle: result.vehicle_id,
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
      subtitle="Stacked view of the present value cost drivers for each vehicle."
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12 }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, { maximumFractionDigits: 0 })
            }
            tick={{ fontSize: 12 }}
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
