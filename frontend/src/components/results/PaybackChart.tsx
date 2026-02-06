import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
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
const PAYBACK_COLOR = '#FFC700';

// 15-year vehicle life (from constants)
const VEHICLE_LIFE = 15;

interface CumulativeCostData {
  year: number;
  diesel: number;
  bev: number;
}

const PaybackTooltip = ({ active, payload, label }: TooltipProps<ValueType, NameType>) => {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">Year {label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value as number)}
        </p>
      ))}
    </div>
  );
};

const PaybackChart = () => {
  const results = useTCOStore((state) => state.results);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  if (!results.length) {
    return (
      <Card
        title="Payback timeline"
        subtitle="When does switching to electric break even?"
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
        title="Payback timeline"
        subtitle="When does switching to electric break even?"
      >
        <div className="flex h-64 items-center justify-center border-2 border-dashed border-slate-200 rounded-lg">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see payback timeline
          </p>
        </div>
      </Card>
    );
  }

  const dieselName = vehicleDetails[dieselResult.vehicle_id]?.model_name ?? 'Diesel';
  const bevName = vehicleDetails[bevResult.vehicle_id]?.model_name ?? 'Electric';

  // Calculate cumulative costs for each year
  // Using annual_cost as the yearly operating cost, scaled from total_cost
  const dieselAnnualCost = dieselResult.annual_cost;
  const bevAnnualCost = bevResult.annual_cost;

  // Upfront costs are purchase_cost only (which includes stamp duty but excludes financing_cost).
  // financing_cost is the total nominal interest over the loan term, NOT an upfront amount.
  const dieselUpfront = dieselResult.breakdown.upfront_costs.purchase_cost;
  const bevUpfront = bevResult.breakdown.upfront_costs.purchase_cost;

  // Calculate cumulative costs over the vehicle life
  const data: CumulativeCostData[] = [];
  let dieselCumulative = dieselUpfront;
  let bevCumulative = bevUpfront;

  for (let year = 0; year <= VEHICLE_LIFE; year++) {
    if (year === 0) {
      data.push({ year, diesel: dieselUpfront, bev: bevUpfront });
    } else {
      dieselCumulative += dieselAnnualCost;
      bevCumulative += bevAnnualCost;
      data.push({ year, diesel: dieselCumulative, bev: bevCumulative });
    }
  }

  // Find payback year (where BEV becomes cheaper)
  let paybackYear: number | null = null;
  for (let i = 1; i < data.length; i++) {
    const prev = data[i - 1];
    const curr = data[i];
    // Check if BEV crosses below diesel in this year
    if (prev.bev >= prev.diesel && curr.bev < curr.diesel) {
      // Linear interpolation for more accurate payback point
      const dieselSlope = curr.diesel - prev.diesel;
      const bevSlope = curr.bev - prev.bev;
      const slopeDiff = dieselSlope - bevSlope;

      // Guard against equal slopes (parallel lines) which would cause division by zero
      // This should be rare since we already detected a crossing, but guard defensively
      if (Math.abs(slopeDiff) < 0.01) {
        // Lines are nearly parallel - use the midpoint of the crossing year
        paybackYear = prev.year + 0.5;
      } else {
        const yearFraction = (prev.bev - prev.diesel) / slopeDiff;
        paybackYear = prev.year + yearFraction;
      }
      break;
    }
  }

  // If BEV starts cheaper, payback is immediate
  if (data[0].bev < data[0].diesel) {
    paybackYear = 0;
  }

  // Calculate total savings at end of life
  const finalDiesel = data[data.length - 1].diesel;
  const finalBev = data[data.length - 1].bev;
  const totalSavings = finalDiesel - finalBev;

  return (
    <Card
      title="Payback timeline"
      subtitle="Cumulative cost comparison (upfront purchase + annual operating costs)"
    >
      <div className="mb-4">
        {paybackYear !== null ? (
          <p className="text-sm text-slate-600">
            Electric breaks even at <span className="font-semibold text-black">year {paybackYear.toFixed(1)}</span>
            {totalSavings > 0 && (
              <>, saving <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over {VEHICLE_LIFE} years</>
            )}
          </p>
        ) : totalSavings > 0 ? (
          <p className="text-sm text-slate-600">
            Electric saves <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over {VEHICLE_LIFE} years
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            Diesel remains cheaper over the {VEHICLE_LIFE}-year horizon
          </p>
        )}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12, fill: '#000000' }}
            label={{ value: 'Year', position: 'insideBottom', offset: -5, fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(value) => formatCurrency(value as number, { maximumFractionDigits: 0 })}
            tick={{ fontSize: 12, fill: '#000000' }}
          />
          <Tooltip content={<PaybackTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />

          {paybackYear !== null && paybackYear > 0 && paybackYear < VEHICLE_LIFE && (
            <ReferenceLine
              x={paybackYear}
              stroke={PAYBACK_COLOR}
              strokeWidth={2}
              strokeDasharray="4 4"
              label={{
                value: `Payback: Year ${paybackYear.toFixed(1)}`,
                position: 'top',
                fontSize: 11,
                fill: '#000000',
              }}
            />
          )}

          <Line
            type="monotone"
            dataKey="diesel"
            name={dieselName}
            stroke={DIESEL_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="bev"
            name={bevName}
            stroke={ELECTRIC_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default PaybackChart;
