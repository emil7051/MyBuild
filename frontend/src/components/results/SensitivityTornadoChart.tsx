import { useMemo } from 'react';
import Card from '@components/shared/Card';
import type { CalculationResponsePayload, VehicleDetail } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// Brand colors
const LOW_COLOR = '#EA5300'; // Diesel orange for adverse scenario
const HIGH_COLOR = '#00FFC7'; // Electric aqua for favorable scenario
const BASELINE_COLOR = '#000000';

interface SensitivityItem {
  parameter: string;
  lowDelta: number;
  highDelta: number;
}

interface TornadoBarData {
  parameter: string;
  lowValue: number;
  highValue: number;
  lowDelta: number;
  highDelta: number;
}

interface SensitivityTornadoChartProps {
  results: CalculationResponsePayload[];
  vehicleDetails: Record<string, VehicleDetail>;
}

const TornadoTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as TornadoBarData;

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.parameter}</p>
      <p style={{ color: LOW_COLOR }}>
        -20%: {entry.lowDelta >= 0 ? '+' : ''}{formatCurrency(entry.lowDelta)} savings
      </p>
      <p style={{ color: HIGH_COLOR }}>
        +20%: {entry.highDelta >= 0 ? '+' : ''}{formatCurrency(entry.highDelta)} savings
      </p>
      <p className="mt-1 text-slate-500 italic">Linear approximation</p>
    </div>
  );
};

const SensitivityTornadoChart = ({
  results,
  vehicleDetails,
}: SensitivityTornadoChartProps) => {
  const chartAnalysis = useMemo(() => {
    const dieselResult = results.find(
      (result) => vehicleDetails[result.vehicle_id]?.drivetrain_type === 'Diesel'
    );
    const bevResult = results.find(
      (result) => vehicleDetails[result.vehicle_id]?.drivetrain_type === 'BEV'
    );
    if (!dieselResult || !bevResult) {
      return undefined;
    }

    const sensitivities: SensitivityItem[] = [
      {
        parameter: 'Fuel price',
        lowDelta: -(dieselResult.breakdown.npv_costs.fuel_cost * 0.2),
        highDelta: dieselResult.breakdown.npv_costs.fuel_cost * 0.2,
      },
      {
        parameter: 'Electricity price',
        lowDelta: bevResult.breakdown.npv_costs.fuel_cost * 0.2,
        highDelta: -(bevResult.breakdown.npv_costs.fuel_cost * 0.2),
      },
      {
        parameter: 'Annual kms',
        lowDelta: -(
          (dieselResult.breakdown.npv_costs.fuel_cost - bevResult.breakdown.npv_costs.fuel_cost) *
          0.2
        ),
        highDelta:
          (dieselResult.breakdown.npv_costs.fuel_cost - bevResult.breakdown.npv_costs.fuel_cost) *
          0.2,
      },
      {
        parameter: 'Maintenance cost',
        lowDelta: -(
          (dieselResult.breakdown.npv_costs.maintenance_cost -
            bevResult.breakdown.npv_costs.maintenance_cost) *
          0.2
        ),
        highDelta:
          (dieselResult.breakdown.npv_costs.maintenance_cost -
            bevResult.breakdown.npv_costs.maintenance_cost) *
          0.2,
      },
      {
        parameter: 'Battery replacement',
        lowDelta: bevResult.breakdown.npv_costs.battery_replacement_cost * 0.2,
        highDelta: -(bevResult.breakdown.npv_costs.battery_replacement_cost * 0.2),
      },
      {
        parameter: 'Purchase price',
        lowDelta: bevResult.breakdown.upfront_costs.purchase_cost * 0.2,
        highDelta: -(bevResult.breakdown.upfront_costs.purchase_cost * 0.2),
      },
    ];

    const significantSensitivities = sensitivities
      .filter((sensitivity) =>
        Math.abs(sensitivity.lowDelta) > 500 || Math.abs(sensitivity.highDelta) > 500
      )
      .sort((left, right) => {
        const leftSpread = Math.abs(left.highDelta - left.lowDelta);
        const rightSpread = Math.abs(right.highDelta - right.lowDelta);
        return rightSpread - leftSpread;
      })
      .slice(0, 6);

    const data: TornadoBarData[] = significantSensitivities.map((sensitivity) => ({
      parameter: sensitivity.parameter,
      lowValue: sensitivity.lowDelta < 0 ? sensitivity.lowDelta : 0,
      highValue: sensitivity.highDelta > 0 ? sensitivity.highDelta : 0,
      lowDelta: sensitivity.lowDelta,
      highDelta: sensitivity.highDelta,
    }));

    const allValues = data.flatMap((entry) => [entry.lowDelta, entry.highDelta]);
    const minVal = Math.min(...allValues, 0);
    const maxVal = Math.max(...allValues, 0);
    const absMax = Math.max(Math.abs(minVal), Math.abs(maxVal));

    return {
      data,
      absMax,
      domainPadding: absMax * 0.15,
    };
  }, [results, vehicleDetails]);

  if (!results.length) {
    return (
      <Card
        title="Sensitivity analysis"
        subtitle="How do assumptions affect the comparison?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  if (!chartAnalysis) {
    return (
      <Card
        title="Sensitivity analysis"
        subtitle="How do assumptions affect the comparison?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see sensitivity analysis
          </p>
        </div>
      </Card>
    );
  }

  const { data, absMax, domainPadding } = chartAnalysis;

  return (
    <Card
      title="Sensitivity analysis (approximate)"
      subtitle="How do assumptions affect the comparison?"
    >
      <div className="mb-4">
        <p className="text-sm text-slate-600">
          Estimated impact of +/- 20% change in each parameter on BEV savings.
          Values are linearly scaled from baseline costs and may not reflect
          nonlinear effects (e.g., battery replacement timing, financing terms).
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 100, bottom: 10 }}
        >
          <CartesianGrid stroke="#E5E5E5" horizontal={false} />
          <XAxis
            type="number"
            domain={[-absMax - domainPadding, absMax + domainPadding]}
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 11, fill: '#000000' }}
          />
          <YAxis
            type="category"
            dataKey="parameter"
            tick={{ fontSize: 12, fill: '#000000' }}
            width={95}
          />
          <Tooltip content={<TornadoTooltip />} />
          <ReferenceLine x={0} stroke={BASELINE_COLOR} strokeWidth={2} />

          {/* Low scenario bars (extending left) */}
          <Bar dataKey="lowDelta" radius={[4, 4, 4, 4]} maxBarSize={24}>
            {data.map((entry, index) => (
              <Cell
                key={`low-${index}`}
                fill={entry.lowDelta < 0 ? LOW_COLOR : HIGH_COLOR}
              />
            ))}
          </Bar>

          {/* High scenario bars (extending right) - rendered on same axis */}
          <Bar dataKey="highDelta" radius={[4, 4, 4, 4]} maxBarSize={24}>
            {data.map((entry, index) => (
              <Cell
                key={`high-${index}`}
                fill={entry.highDelta > 0 ? HIGH_COLOR : LOW_COLOR}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: HIGH_COLOR }} />
          <span>BEV savings increase</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: LOW_COLOR }} />
          <span>BEV savings decrease</span>
        </div>
      </div>
    </Card>
  );
};

export default SensitivityTornadoChart;
