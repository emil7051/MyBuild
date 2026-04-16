import React from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterAll, beforeAll, beforeEach, describe, it, vi } from 'vitest';
import { useTCOStore } from '@state/tcoStore';
import type { CalculationResponsePayload, CostBreakdown, VehicleDetail, WizardData } from '@shared/types/tco.types';
import ResultsPanel from '@components/results/ResultsPanel';

vi.mock('@components/results/ComparisonHighlights', () => ({
  default: () => 'Highlights chart rendered',
}));

vi.mock('@components/results/CostPerKmChart', () => ({
  default: () => {
    throw new Error('CostPerKmChart exploded');
  },
}));

vi.mock('@components/results/CostBreakdownChart', () => ({
  default: () => 'Cost components chart rendered',
}));

vi.mock('@components/results/PaybackChart', () => ({
  default: () => 'Payback chart rendered',
}));

vi.mock('@components/results/SavingsWaterfallChart', () => ({
  default: () => 'Savings chart rendered',
}));

vi.mock('@components/results/SensitivityTornadoChart', () => ({
  default: () => 'Sensitivity chart rendered',
}));

const globalReactAct = globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean };
const previousActEnvironment = globalReactAct.IS_REACT_ACT_ENVIRONMENT;

const baseWizardData: WizardData = {
  currentVehicle: 'DIESEL-A',
  comparisonVehicles: ['BEV-A'],
  scenario: 'baseline',
  purchaseMethod: 'financed',
  dutyCycle: {
    urban: 60,
    regional: 25,
    longHaul: 15,
  },
  overrides: {},
  vehicleParamOverrides: {},
};

const breakdownTemplate: CostBreakdown = {
  npv_costs: {
    fuel_cost: 0,
    maintenance_cost: 0,
    battery_replacement_cost: 0,
    carbon_cost: 0,
    charging_labour_cost: 0,
    payload_penalty_cost: 0,
    payload_trip_multiplier_cost: 0,
    charging_dwell_opportunity_cost: 0,
    mr_downtime_opportunity_cost: 0,
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
};

const createResult = (vehicleId: string): CalculationResponsePayload => ({
  vehicle_id: vehicleId,
  scenario_name: 'baseline',
  total_cost: 100_000,
  annual_cost: 10_000,
  cost_per_km: 1.0,
  breakdown: breakdownTemplate,
});

const createVehicleDetail = (
  vehicleId: string,
  modelName: string,
  drivetrainType: VehicleDetail['drivetrain_type']
): VehicleDetail => ({
  vehicle_id: vehicleId,
  model_name: modelName,
  drivetrain_type: drivetrainType,
  weight_class: 'Medium Rigid',
  comparison_pair: 'PAIR',
  payload: 0,
  msrp: 0,
  range_km: 0,
  battery_capacity_kwh: 0,
  kwh_per_km: 0,
  litres_per_km: 0,
  annual_registration: 0,
  annual_kms: 0,
});

const waitForText = async (
  container: HTMLElement,
  text: string,
  timeoutMs = 2000
): Promise<void> => {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    if (container.textContent?.includes(text)) {
      return;
    }

    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
  }

  throw new Error(
    `Timed out waiting for text: ${text}\nCurrent content: ${container.textContent ?? '<empty>'}`
  );
};

describe('ResultsPanel chart isolation', () => {
  beforeAll(() => {
    globalReactAct.IS_REACT_ACT_ENVIRONMENT = true;
  });

  afterAll(() => {
    globalReactAct.IS_REACT_ACT_ENVIRONMENT = previousActEnvironment;
  });

  beforeEach(() => {
    useTCOStore.setState((state) => ({
      wizardData: baseWizardData,
      results: [createResult('DIESEL-A'), createResult('BEV-A')],
      isCalculating: false,
      calculationInFlightCount: 0,
      vehicleDetails: {
        ...state.vehicleDetails,
        'DIESEL-A': createVehicleDetail('DIESEL-A', 'Diesel Alpha', 'Diesel'),
        'BEV-A': createVehicleDetail('BEV-A', 'BEV Beta', 'BEV'),
      },
    }));
  });

  it('keeps other charts visible when one chart throws', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const container = document.createElement('div');
    document.body.appendChild(container);
    const root: Root = createRoot(container);

    try {
      await act(async () => {
        root.render(React.createElement(ResultsPanel));
      });

      await waitForText(container, 'We could not render this chart right now.');
      await waitForText(container, 'Cost components chart rendered');
      await waitForText(container, 'Highlights chart rendered');
    } finally {
      await act(async () => {
        root.unmount();
      });
      container.remove();
      consoleErrorSpy.mockRestore();
    }
  });
});
