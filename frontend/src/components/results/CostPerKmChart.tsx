import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency, formatPerKilometre } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

const CostTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as {
    vehicle: string;
    costPerKm: number;
    annualCost: number;
    totalCost: number;
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.vehicle}</p>
      <p>{formatPerKilometre(entry.costPerKm)}</p>
      <p>Annual {formatCurrency(entry.annualCost)}</p>
      <p>Lifetime {formatCurrency(entry.totalCost)}</p>
    </div>
  );
};

const CostPerKmChart = () => {
  const results = useTCOStore((state) => state.results);

  if (!results.length) {
    return null;
  }

  const data = results.map((result) => ({
    vehicle: result.vehicle_id,
    costPerKm: Number(result.cost_per_km.toFixed(4)),
    annualCost: result.annual_cost,
    totalCost: result.total_cost,
  }));

  return (
    <Card
      title="Cost per kilometre"
      subtitle="Lower bars indicate cheaper ownership under the selected scenario."
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12 }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })
            }
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CostTooltip />} />
          <Bar
            dataKey="costPerKm"
            name="Cost per km"
            fill="#124df0"
            radius={[8, 8, 0, 0]}
            maxBarSize={64}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostPerKmChart;
