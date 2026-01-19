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
const SAVINGS_COLOR = '#00FFC7'; // Electric/positive
const EXTRA_COST_COLOR = '#EA5300'; // Diesel/negative
const TOTAL_COLOR = '#FFC700'; // Winner/total

interface WaterfallItem {
  name: string;
  value: number;
  displayValue: number;
  isTotal?: boolean;
  isPositive?: boolean;
  start: number;
  end: number;
}

const WaterfallTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0].payload as WaterfallItem;
  const isPositive = entry.value > 0;
  const label = entry.isTotal
    ? 'Net savings'
    : isPositive
      ? 'BEV saves'
      : 'BEV costs more';

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">{entry.name}</p>
      <p>
        {label}: {formatCurrency(Math.abs(entry.value))}
      </p>
    </div>
  );
};

const SavingsWaterfallChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Savings breakdown"
        subtitle="What drives the cost difference?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  // Find diesel and BEV results deterministically:
  // - Diesel: use first diesel result (baseline)
  // - BEV: use the BEV with the lowest total_cost (best option)
  const dieselResults = results.filter((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResults = results.filter((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  const dieselResult = dieselResults[0];
  // Sort BEVs by total_cost ascending and take the best one
  const bevResult = bevResults.length > 0
    ? [...bevResults].sort((a, b) => a.total_cost - b.total_cost)[0]
    : undefined;

  if (!dieselResult || !bevResult) {
    return (
      <Card
        title="Savings breakdown"
        subtitle="What drives the cost difference?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see savings breakdown
          </p>
        </div>
      </Card>
    );
  }

  // Calculate savings for each cost category (positive = BEV saves money)
  // NOTE: We exclude financing_cost from the breakdown because it's a nominal lifetime
  // total (not NPV-adjusted), unlike most other categories. The total_cost comparison
  // still correctly captures the full picture including financing effects.
  const categories = [
    {
      name: 'Fuel / Energy',
      diesel: dieselResult.breakdown.fuel_cost,
      bev: bevResult.breakdown.fuel_cost,
    },
    {
      name: 'Maintenance',
      diesel: dieselResult.breakdown.maintenance_cost,
      bev: bevResult.breakdown.maintenance_cost,
    },
    {
      name: 'Purchase',
      diesel: dieselResult.breakdown.purchase_cost,
      bev: bevResult.breakdown.purchase_cost,
    },
    {
      name: 'Carbon',
      diesel: dieselResult.breakdown.carbon_cost,
      bev: bevResult.breakdown.carbon_cost,
    },
    {
      name: 'Insurance',
      diesel: dieselResult.breakdown.insurance_cost,
      bev: bevResult.breakdown.insurance_cost,
    },
    {
      name: 'Battery',
      diesel: dieselResult.breakdown.battery_replacement_cost,
      bev: bevResult.breakdown.battery_replacement_cost,
    },
    {
      name: 'Charging labour',
      diesel: dieselResult.breakdown.charging_labour_cost,
      bev: bevResult.breakdown.charging_labour_cost,
    },
    {
      name: 'Payload penalty',
      diesel: dieselResult.breakdown.payload_penalty_cost,
      bev: bevResult.breakdown.payload_penalty_cost,
    },
  ].map((cat) => ({
    name: cat.name,
    savings: cat.diesel - cat.bev, // Positive means BEV saves
  }));

  // Filter out zero or very small values
  const significantCategories = categories.filter(
    (cat) => Math.abs(cat.savings) > 100
  );

  // Sort by absolute value (largest impact first)
  significantCategories.sort((a, b) => Math.abs(b.savings) - Math.abs(a.savings));

  // Build waterfall data
  let runningTotal = 0;
  const data: WaterfallItem[] = significantCategories.map((cat) => {
    const start = runningTotal;
    runningTotal += cat.savings;
    return {
      name: cat.name,
      value: cat.savings,
      displayValue: cat.savings,
      isPositive: cat.savings > 0,
      start: cat.savings > 0 ? start : runningTotal,
      end: cat.savings > 0 ? runningTotal : start,
    };
  });

  // Add total bar
  const totalSavings = dieselResult.total_cost - bevResult.total_cost;
  data.push({
    name: 'Net savings',
    value: totalSavings,
    displayValue: totalSavings,
    isTotal: true,
    isPositive: totalSavings > 0,
    start: 0,
    end: totalSavings,
  });

  // Calculate domain for Y axis
  const allValues = data.flatMap((d) => [d.start, d.end]);
  const minVal = Math.min(...allValues, 0);
  const maxVal = Math.max(...allValues, 0);
  const padding = Math.abs(maxVal - minVal) * 0.1;

  const getBarColor = (entry: WaterfallItem) => {
    if (entry.isTotal) return TOTAL_COLOR;
    return entry.value > 0 ? SAVINGS_COLOR : EXTRA_COST_COLOR;
  };

  return (
    <Card
      title="Savings breakdown"
      subtitle="What drives the cost difference?"
    >
      <div className="mb-4">
        <p className="text-sm text-slate-600">
          {totalSavings > 0 ? (
            <>
              Electric saves{' '}
              <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span>{' '}
              over the vehicle lifetime
            </>
          ) : totalSavings < 0 ? (
            <>
              Diesel saves{' '}
              <span className="font-semibold text-black">{formatCurrency(Math.abs(totalSavings))}</span>{' '}
              over the vehicle lifetime
            </>
          ) : (
            <>Both options have similar total costs</>
          )}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#000000' }}
            angle={-30}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 12, fill: '#000000' }}
            domain={[minVal - padding, maxVal + padding]}
          />
          <Tooltip content={<WaterfallTooltip />} />
          <ReferenceLine y={0} stroke="#000000" strokeWidth={1} />

          {/* For waterfall effect, we use stacked bars with transparent base */}
          <Bar dataKey="start" stackId="stack" fill="transparent" />
          <Bar dataKey="displayValue" stackId="stack" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry)}
                stroke={entry.isTotal ? '#000000' : undefined}
                strokeWidth={entry.isTotal ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: SAVINGS_COLOR }} />
          <span>BEV saves</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded" style={{ backgroundColor: EXTRA_COST_COLOR }} />
          <span>BEV costs more</span>
        </div>
      </div>
    </Card>
  );
};

export default SavingsWaterfallChart;
