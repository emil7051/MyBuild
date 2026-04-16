import { useMemo } from 'react';
import Card from '@components/shared/Card';
import type { CalculationResponsePayload } from '@shared/types/tco.types';
import type { VehicleDetail } from '@shared/types/tco.types';
import { calculatePresentValue } from '@shared/calculator/math';
import { CONSTANTS } from '@shared/data/constants';
import { formatCurrency } from '@utils/format';
import EmptyChartState from './EmptyChartState';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

// Brand-aligned cost colors
const COST_COLORS = {
  purchase_financing_npv: '#3040B9',
  fuel_cost: '#3B52FF',
  maintenance_cost: '#7080FF',
  insurance_cost: '#B9C2FF',
  registration_cost: '#844A34',
  battery_replacement_cost: '#005A46',
  carbon_cost: '#F2AE95',
  charging_labour_cost: '#00FFC7',
  payload_penalty_cost: '#C5FFF3',
  payload_trip_multiplier_cost: '#F97316',
  charging_dwell_opportunity_cost: '#8B5CF6',
  mr_downtime_opportunity_cost: '#06B6D4',
  residual_value_credit: '#1E8E5A',
} as const;

type BreakdownSeriesItem = {
  key: keyof typeof COST_COLORS;
  label: string;
  color: string;
};

const breakdownSeries: BreakdownSeriesItem[] = [
  {
    key: 'purchase_financing_npv',
    label: 'Purchase + financing (NPV)',
    color: COST_COLORS.purchase_financing_npv,
  },
  {
    key: 'fuel_cost',
    label: 'Fuel / Energy',
    color: COST_COLORS.fuel_cost,
  },
  {
    key: 'maintenance_cost',
    label: 'Maintenance',
    color: COST_COLORS.maintenance_cost,
  },
  {
    key: 'insurance_cost',
    label: 'Insurance (NPV)',
    color: COST_COLORS.insurance_cost,
  },
  {
    key: 'registration_cost',
    label: 'Registration (NPV)',
    color: COST_COLORS.registration_cost,
  },
  {
    key: 'battery_replacement_cost',
    label: 'Battery replacement',
    color: COST_COLORS.battery_replacement_cost,
  },
  {
    key: 'carbon_cost',
    label: 'Carbon',
    color: COST_COLORS.carbon_cost,
  },
  {
    key: 'charging_labour_cost',
    label: 'Charging labour',
    color: COST_COLORS.charging_labour_cost,
  },
  {
    key: 'payload_penalty_cost',
    label: 'Payload penalty',
    color: COST_COLORS.payload_penalty_cost,
  },
  {
    key: 'payload_trip_multiplier_cost',
    label: 'Payload Trip Multiplier',
    color: COST_COLORS.payload_trip_multiplier_cost,
  },
  {
    key: 'charging_dwell_opportunity_cost',
    label: 'Charging Dwell Opportunity',
    color: COST_COLORS.charging_dwell_opportunity_cost,
  },
  {
    key: 'mr_downtime_opportunity_cost',
    label: 'M&R Downtime Opportunity',
    color: COST_COLORS.mr_downtime_opportunity_cost,
  },
  {
    key: 'residual_value_credit',
    label: 'Residual value credit',
    color: COST_COLORS.residual_value_credit,
  },
];

const DISCOUNT_RATE = CONSTANTS.DISCOUNT_RATE as number;
const VEHICLE_LIFE = CONSTANTS.VEHICLE_LIFE as number;

const normaliseCurrencyValue = (value: number): number => (Math.abs(value) < 1e-6 ? 0 : value);

const convertNominalLifetimeToNpv = (nominalLifetimeCost: number): number => {
  if (VEHICLE_LIFE <= 0) {
    return nominalLifetimeCost;
  }

  const annualCost = nominalLifetimeCost / VEHICLE_LIFE;
  return calculatePresentValue(annualCost, VEHICLE_LIFE, DISCOUNT_RATE);
};

// Info tooltip explaining NPV-converted value bases in the breakdown chart
const NpvAlignedInfo = () => (
  <span className="inline-flex items-center gap-1">
    NPV-aligned components that sum to total cost.
    <span className="group relative cursor-help">
      <svg
        className="h-4 w-4 text-slate-400 hover:text-slate-600 transition-colors"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span className="invisible group-hover:visible absolute left-1/2 -translate-x-1/2 top-6 z-10 w-72 rounded-md bg-slate-800 px-3 py-2 text-xs text-white shadow-lg">
        <span className="font-semibold block mb-1">Chart basis:</span>
        <span className="block mb-1">
          Every segment is displayed on an NPV basis and the stacked total equals
          the vehicle&apos;s reported total cost.
        </span>
        <span className="block mb-1">
          Insurance and registration are converted from nominal lifetime totals to
          NPV using the model discount rate and horizon.
        </span>
        <span className="block">
          Residual value is shown as a negative credit.
        </span>
        <span className="absolute -top-1 left-1/2 -translate-x-1/2 border-4 border-transparent border-b-slate-800" />
      </span>
    </span>
  </span>
);

interface CostBreakdownChartProps {
  results: CalculationResponsePayload[];
  vehicleDetails: Record<string, VehicleDetail>;
}

const CostBreakdownChart = ({ results, vehicleDetails }: CostBreakdownChartProps) => {
  const data = useMemo(
    () => {
      if (!results.length) {
        return [];
      }

      return results.map((result) => {
        const insuranceCostNpv = convertNominalLifetimeToNpv(result.breakdown.nominal_costs.insurance_cost);
        const registrationCostNpv = convertNominalLifetimeToNpv(
          result.breakdown.nominal_costs.registration_cost
        );
        const residualValueCredit = -result.breakdown.npv_costs.residual_value;
        const variableAndFixedNpvWithoutPurchase =
          result.breakdown.npv_costs.fuel_cost +
          result.breakdown.npv_costs.maintenance_cost +
          insuranceCostNpv +
          registrationCostNpv +
          result.breakdown.npv_costs.battery_replacement_cost +
          result.breakdown.npv_costs.carbon_cost +
          result.breakdown.npv_costs.charging_labour_cost +
          result.breakdown.npv_costs.payload_penalty_cost +
          result.breakdown.npv_costs.payload_trip_multiplier_cost +
          result.breakdown.npv_costs.charging_dwell_opportunity_cost +
          result.breakdown.npv_costs.mr_downtime_opportunity_cost +
          residualValueCredit;
        const purchaseFinancingNpv = result.total_cost - variableAndFixedNpvWithoutPurchase;

        const entry: Record<string, number | string> = {
          vehicle: vehicleDetails[result.vehicle_id]?.model_name ?? result.vehicle_id,
          purchase_financing_npv: normaliseCurrencyValue(purchaseFinancingNpv),
          fuel_cost: normaliseCurrencyValue(result.breakdown.npv_costs.fuel_cost),
          maintenance_cost: normaliseCurrencyValue(result.breakdown.npv_costs.maintenance_cost),
          insurance_cost: normaliseCurrencyValue(insuranceCostNpv),
          registration_cost: normaliseCurrencyValue(registrationCostNpv),
          battery_replacement_cost: normaliseCurrencyValue(
            result.breakdown.npv_costs.battery_replacement_cost
          ),
          carbon_cost: normaliseCurrencyValue(result.breakdown.npv_costs.carbon_cost),
          charging_labour_cost: normaliseCurrencyValue(result.breakdown.npv_costs.charging_labour_cost),
          payload_penalty_cost: normaliseCurrencyValue(result.breakdown.npv_costs.payload_penalty_cost),
          payload_trip_multiplier_cost: normaliseCurrencyValue(
            result.breakdown.npv_costs.payload_trip_multiplier_cost
          ),
          charging_dwell_opportunity_cost: normaliseCurrencyValue(
            result.breakdown.npv_costs.charging_dwell_opportunity_cost
          ),
          mr_downtime_opportunity_cost: normaliseCurrencyValue(
            result.breakdown.npv_costs.mr_downtime_opportunity_cost
          ),
          residual_value_credit: normaliseCurrencyValue(residualValueCredit),
        };

        return entry;
      });
    },
    [results, vehicleDetails]
  );

  if (!results.length) {
    return (
      <Card
        title="Cost components"
        subtitle={<NpvAlignedInfo />}
      >
        <EmptyChartState message="No results to display" />
      </Card>
    );
  }

  return (
    <Card
      title="Cost components"
      subtitle={<NpvAlignedInfo />}
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#E5E5E5" vertical={false} />
          <ReferenceLine y={0} stroke="#94A3B8" strokeWidth={1} />
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
