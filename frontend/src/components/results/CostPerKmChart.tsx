import { useMemo } from 'react';
import Card from '@components/shared/Card';
import type { CalculationResponsePayload, VehicleDetail } from '@shared/types/tco.types';
import { formatCurrency, formatPerKilometre } from '@utils/format';
import EmptyChartState from './EmptyChartState';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const DIESEL_COLOR = '#EA5300';
const ELECTRIC_COLOR = '#00FFC7';
const WINNER_COLOR = '#FFC700';

type CostTooltipProps = TooltipProps<ValueType, NameType> & {
  payload?: Array<{
    payload: {
      vehicle: string;
      costPerKm: number;
      annualCost: number;
      totalCost: number;
    };
  }>;
};

const CostTooltip = ({ active, payload }: CostTooltipProps) => {
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
      <p>Total cost {formatCurrency(entry.totalCost)}</p>
    </div>
  );
};

interface CostPerKmChartProps {
  results: CalculationResponsePayload[];
  vehicleDetails: Record<string, VehicleDetail>;
}

const CostPerKmChart = ({ results, vehicleDetails }: CostPerKmChartProps) => {
  const data = useMemo(() => {
    if (!results.length) {
      return [];
    }

    const minCostPerKm = Math.min(...results.map((result) => result.cost_per_km));
    return results.map((result) => {
      const detail = vehicleDetails[result.vehicle_id];
      const drivetrainType = detail?.drivetrain_type ?? 'Diesel';
      const isWinner = result.cost_per_km === minCostPerKm;

      return {
        vehicle: detail?.model_name ?? result.vehicle_id,
        costPerKm: Number(result.cost_per_km.toFixed(4)),
        annualCost: result.annual_cost,
        totalCost: result.total_cost,
        drivetrainType,
        isWinner,
      };
    });
  }, [results, vehicleDetails]);

  if (!results.length) {
    return (
      <Card
        title="Cost per kilometre"
        subtitle="Lower bars indicate cheaper ownership under the selected scenario."
      >
        <EmptyChartState message="No results to display" />
      </Card>
    );
  }

  const getBarColor = (entry: (typeof data)[number]) => {
    if (entry.isWinner) return WINNER_COLOR;
    return entry.drivetrainType === 'BEV' ? ELECTRIC_COLOR : DIESEL_COLOR;
  };

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
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis dataKey="vehicle" tick={{ fontSize: 12, fill: '#000000' }} />
          <YAxis
            tickFormatter={(value) =>
              formatCurrency(value as number, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })
            }
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip content={<CostTooltip />} />
          <Bar dataKey="costPerKm" name="Cost per km" radius={[6, 6, 0, 0]} maxBarSize={64}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry)}
                stroke={entry.isWinner ? '#000000' : undefined}
                strokeWidth={entry.isWinner ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostPerKmChart;
