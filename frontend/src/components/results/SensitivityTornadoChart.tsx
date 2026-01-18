import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
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
  baselineSavings: number;
}

interface TornadoBarData {
  parameter: string;
  lowValue: number;
  highValue: number;
  lowDelta: number;
  highDelta: number;
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
    </div>
  );
};

const SensitivityTornadoChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

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

  // Find diesel and BEV results
  const dieselResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  if (!dieselResult || !bevResult) {
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

  // Baseline savings (positive = BEV cheaper)
  const baselineSavings = dieselResult.total_cost - bevResult.total_cost;

  // Calculate sensitivity for each parameter
  // We estimate how +/- 20% change affects the BEV vs Diesel comparison
  const sensitivities: SensitivityItem[] = [
    {
      parameter: 'Fuel price',
      // Higher fuel price benefits BEV (more diesel savings)
      lowDelta: -(dieselResult.breakdown.fuel_cost * 0.2),
      highDelta: dieselResult.breakdown.fuel_cost * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Electricity price',
      // Higher electricity price hurts BEV
      lowDelta: bevResult.breakdown.fuel_cost * 0.2,
      highDelta: -(bevResult.breakdown.fuel_cost * 0.2),
      baselineSavings,
    },
    {
      parameter: 'Annual kms',
      // More kms amplifies operating cost differences
      // If BEV has lower operating costs, more kms = more savings
      lowDelta: -((dieselResult.breakdown.fuel_cost - bevResult.breakdown.fuel_cost) * 0.2),
      highDelta: (dieselResult.breakdown.fuel_cost - bevResult.breakdown.fuel_cost) * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Maintenance cost',
      // Higher maintenance costs hurt diesel more (they're higher baseline)
      lowDelta: -(dieselResult.breakdown.maintenance_cost - bevResult.breakdown.maintenance_cost) * 0.2,
      highDelta: (dieselResult.breakdown.maintenance_cost - bevResult.breakdown.maintenance_cost) * 0.2,
      baselineSavings,
    },
    {
      parameter: 'Battery replacement',
      // Only affects BEV
      lowDelta: bevResult.breakdown.battery_replacement_cost * 0.2,
      highDelta: -(bevResult.breakdown.battery_replacement_cost * 0.2),
      baselineSavings,
    },
    {
      parameter: 'Purchase price',
      // BEV usually more expensive, so lower price helps BEV
      lowDelta: bevResult.breakdown.purchase_cost * 0.2,
      highDelta: -(bevResult.breakdown.purchase_cost * 0.2),
      baselineSavings,
    },
  ];

  // Filter to significant sensitivities and sort by impact
  const significantSensitivities = sensitivities
    .filter((s) => Math.abs(s.lowDelta) > 500 || Math.abs(s.highDelta) > 500)
    .sort((a, b) => {
      const aSpread = Math.abs(a.highDelta - a.lowDelta);
      const bSpread = Math.abs(b.highDelta - b.lowDelta);
      return bSpread - aSpread;
    })
    .slice(0, 6); // Top 6 most impactful

  // Build tornado chart data
  const data: TornadoBarData[] = significantSensitivities.map((s) => ({
    parameter: s.parameter,
    lowValue: s.lowDelta < 0 ? s.lowDelta : 0,
    highValue: s.highDelta > 0 ? s.highDelta : 0,
    lowDelta: s.lowDelta,
    highDelta: s.highDelta,
  }));

  // Calculate domain
  const allValues = data.flatMap((d) => [d.lowDelta, d.highDelta]);
  const minVal = Math.min(...allValues, 0);
  const maxVal = Math.max(...allValues, 0);
  const absMax = Math.max(Math.abs(minVal), Math.abs(maxVal));
  const domainPadding = absMax * 0.15;

  return (
    <Card
      title="Sensitivity analysis"
      subtitle="How do assumptions affect the comparison?"
    >
      <div className="mb-4">
        <p className="text-sm text-slate-600">
          Impact of +/- 20% change in each parameter on BEV savings
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
