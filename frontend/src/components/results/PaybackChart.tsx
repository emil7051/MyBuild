import Card from '@components/shared/Card';
import { calculateNominalCostTimeline } from '@shared/calculator';
import type { CalculationRequestPayload } from '@shared/types/tco.types';
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

const DIESEL_COLOR = '#EA5300';
const ELECTRIC_COLOR = '#00FFC7';
const PAYBACK_COLOR = '#FFC700';

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
  const wizardData = useTCOStore((state) => state.wizardData);

  if (!results.length) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200">
          <p className="text-sm text-slate-500">No results to display</p>
        </div>
      </Card>
    );
  }

  const dieselResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'Diesel');
  const bevResult = results.find((r) => vehicleDetails[r.vehicle_id]?.drivetrain_type === 'BEV');

  if (!dieselResult || !bevResult) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200">
          <p className="text-sm text-slate-500">
            Compare both diesel and electric vehicles to see payback timeline
          </p>
        </div>
      </Card>
    );
  }

  const commonPayload = {
    scenario_name: wizardData.scenario,
    purchase_method: wizardData.purchaseMethod,
    duty_cycle: wizardData.dutyCycle,
    overrides: wizardData.overrides,
  } as const;

  const dieselPayload: CalculationRequestPayload = {
    vehicle_id: dieselResult.vehicle_id,
    ...commonPayload,
    vehicle_overrides: wizardData.vehicleParamOverrides?.[dieselResult.vehicle_id],
  };
  const bevPayload: CalculationRequestPayload = {
    vehicle_id: bevResult.vehicle_id,
    ...commonPayload,
    vehicle_overrides: wizardData.vehicleParamOverrides?.[bevResult.vehicle_id],
  };

  const dieselTimeline = calculateNominalCostTimeline(dieselPayload);
  const bevTimeline = calculateNominalCostTimeline(bevPayload);
  const pointCount = Math.min(dieselTimeline.length, bevTimeline.length);
  const data: CumulativeCostData[] = Array.from({ length: pointCount }, (_, idx) => ({
    year: dieselTimeline[idx].year,
    diesel: dieselTimeline[idx].cumulativeCost,
    bev: bevTimeline[idx].cumulativeCost,
  }));

  if (!data.length) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200">
          <p className="text-sm text-slate-500">Unable to build payback timeline.</p>
        </div>
      </Card>
    );
  }

  let paybackYear: number | null = null;
  if (data[0].bev <= data[0].diesel) {
    paybackYear = 0;
  } else {
    for (let i = 1; i < data.length; i += 1) {
      const prev = data[i - 1];
      const curr = data[i];
      const prevDiff = prev.bev - prev.diesel;
      const currDiff = curr.bev - curr.diesel;

      if (prevDiff > 0 && currDiff <= 0) {
        const diffDelta = prevDiff - currDiff;
        paybackYear =
          Math.abs(diffDelta) < 1e-9 ? curr.year : prev.year + prevDiff / diffDelta;
        break;
      }
    }
  }

  const dieselName = vehicleDetails[dieselResult.vehicle_id]?.model_name ?? 'Diesel';
  const bevName = vehicleDetails[bevResult.vehicle_id]?.model_name ?? 'Electric';
  const finalPoint = data[data.length - 1];
  const horizonYears = finalPoint.year;
  const totalSavings = finalPoint.diesel - finalPoint.bev;

  return (
    <Card
      title="Payback timeline"
      subtitle="Cumulative nominal cash costs (upfront purchase, financing schedule, annual operating costs, and residual value)"
    >
      <div className="mb-4">
        {paybackYear !== null ? (
          <p className="text-sm text-slate-600">
            Electric breaks even at <span className="font-semibold text-black">year {paybackYear.toFixed(1)}</span>
            {totalSavings > 0 && (
              <>
                , saving <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over{' '}
                {horizonYears} years
              </>
            )}
          </p>
        ) : totalSavings > 0 ? (
          <p className="text-sm text-slate-600">
            Electric saves <span className="font-semibold text-black">{formatCurrency(totalSavings)}</span> over{' '}
            {horizonYears} years
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            Diesel remains cheaper over the {horizonYears}-year horizon
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

          {paybackYear !== null && paybackYear > 0 && paybackYear < horizonYears && (
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
