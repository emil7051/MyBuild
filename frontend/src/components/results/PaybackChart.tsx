import { useMemo } from 'react';
import Card from '@components/shared/Card';
import { calculateNominalCostTimeline } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  VehicleDetail,
  WizardData,
} from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';
import EmptyChartState from './EmptyChartState';
import { selectComparisonPair } from './comparisonSelection';
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

interface PaybackChartProps {
  results: CalculationResponsePayload[];
  vehicleDetails: Record<string, VehicleDetail>;
  wizardData: WizardData;
}

type PaybackTooltipProps = TooltipProps<ValueType, NameType> & {
  label?: string | number;
  payload?: Array<{
    name?: string;
    value?: number | string;
    color?: string;
  }>;
};

const PaybackTooltip = ({ active, payload, label }: PaybackTooltipProps) => {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow">
      <p className="text-sm font-semibold text-slate-900">Year {label}</p>
      {payload.map((entry, index) => (
        <p key={entry.name ?? `series-${index}`} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value as number)}
        </p>
      ))}
    </div>
  );
};

const PaybackChart = ({ results, vehicleDetails, wizardData }: PaybackChartProps) => {
  const comparisonPair = useMemo(
    () => selectComparisonPair(results, vehicleDetails),
    [results, vehicleDetails]
  );

  const paybackAnalysis = useMemo(() => {
    const dieselResult = comparisonPair?.dieselResult;
    const bevResult = comparisonPair?.bevResult;

    if (!dieselResult || !bevResult) {
      return undefined;
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
    const memoData: CumulativeCostData[] = Array.from({ length: pointCount }, (_, idx) => ({
      year: dieselTimeline[idx].year,
      diesel: dieselTimeline[idx].cumulativeCost,
      bev: bevTimeline[idx].cumulativeCost,
    }));

    let memoPaybackYear: number | null = null;
    if (memoData.length) {
      if (memoData[0].bev <= memoData[0].diesel) {
        memoPaybackYear = 0;
      } else {
        for (let i = 1; i < memoData.length; i += 1) {
          const prev = memoData[i - 1];
          const curr = memoData[i];
          const prevDiff = prev.bev - prev.diesel;
          const currDiff = curr.bev - curr.diesel;

          if (prevDiff > 0 && currDiff <= 0) {
            const diffDelta = prevDiff - currDiff;
            memoPaybackYear =
              Math.abs(diffDelta) < 1e-9 ? curr.year : prev.year + prevDiff / diffDelta;
            break;
          }
        }
      }
    }

    const finalPoint = memoData[memoData.length - 1];
    const memoHorizonYears = finalPoint?.year ?? 0;
    const memoTotalSavings = finalPoint ? finalPoint.diesel - finalPoint.bev : 0;

    return {
      data: memoData,
      paybackYear: memoPaybackYear,
      horizonYears: memoHorizonYears,
      totalSavings: memoTotalSavings,
    };
  }, [comparisonPair, wizardData]);

  if (!results.length) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <EmptyChartState message="No results to display" />
      </Card>
    );
  }

  if (!comparisonPair) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <EmptyChartState message="Compare both diesel and electric vehicles to see payback timeline" />
      </Card>
    );
  }

  if (!paybackAnalysis || !paybackAnalysis.data.length) {
    return (
      <Card title="Payback timeline" subtitle="When does switching to electric break even?">
        <EmptyChartState message="Unable to build payback timeline." />
      </Card>
    );
  }

  const { data, paybackYear, horizonYears, totalSavings } = paybackAnalysis;
  const { dieselResult, bevResult } = comparisonPair;
  const dieselName = vehicleDetails[dieselResult.vehicle_id]?.model_name ?? 'Diesel';
  const bevName = vehicleDetails[bevResult.vehicle_id]?.model_name ?? 'Electric';

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
