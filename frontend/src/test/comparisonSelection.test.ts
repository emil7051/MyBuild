import { describe, expect, it } from 'vitest';
import { VEHICLE_BY_ID } from '@shared/data/vehicleCatalog';
import type { CalculationResponsePayload } from '@shared/types/tco.types';
import {
  COMPARISON_HIGHLIGHTS_POLICY,
  COMPARISON_PAIR_POLICY,
  selectComparisonHighlights,
  selectComparisonPair,
} from '@components/results/comparisonSelection';

const buildResult = (vehicleId: string, totalCost: number): CalculationResponsePayload => ({
  vehicle_id: vehicleId,
  scenario_name: 'baseline',
  total_cost: totalCost,
  annual_cost: totalCost / 10,
  cost_per_km: 1,
  breakdown: {
    npv_costs: {
      fuel_cost: 0,
      maintenance_cost: 0,
      battery_replacement_cost: 0,
      carbon_cost: 0,
      charging_labour_cost: 0,
      payload_penalty_cost: 0,
      residual_value: 0,
    },
    nominal_costs: {
      insurance_cost: 0,
      registration_cost: 0,
      financing_cost: 0,
      depreciation: 0,
    },
    upfront_costs: {
      purchase_cost: 0,
      taxes_and_fees: 0,
    },
  },
});

describe('comparisonSelection', () => {
  it('uses first BEV in result order for diesel-vs-BEV charts', () => {
    const results = [
      buildResult('DSL001', 120_000),
      buildResult('BEV002', 140_000),
      buildResult('BEV001', 100_000),
    ];

    const selection = selectComparisonPair(results, VEHICLE_BY_ID);

    expect(selection).toBeDefined();
    expect(selection?.dieselResult.vehicle_id).toBe('DSL001');
    expect(selection?.bevResult.vehicle_id).toBe('BEV002');
    expect(selection?.policy).toBe(COMPARISON_PAIR_POLICY);
  });

  it('returns undefined pair when diesel or BEV is missing', () => {
    const results = [buildResult('BEV001', 100_000), buildResult('BEV002', 110_000)];

    const selection = selectComparisonPair(results, VEHICLE_BY_ID);

    expect(selection).toBeUndefined();
  });

  it('ranks highlights by overall total cost across all drivetrains', () => {
    const results = [
      buildResult('DSL001', 95_000),
      buildResult('BEV001', 100_000),
      buildResult('BEV002', 105_000),
    ];

    const selection = selectComparisonHighlights(results);

    expect(selection).toBeDefined();
    expect(selection?.leader.vehicle_id).toBe('DSL001');
    expect(selection?.runnerUp?.vehicle_id).toBe('BEV001');
    expect(selection?.policy).toBe(COMPARISON_HIGHLIGHTS_POLICY);
  });

  it('returns undefined highlights selection when no results are present', () => {
    expect(selectComparisonHighlights([])).toBeUndefined();
  });
});
