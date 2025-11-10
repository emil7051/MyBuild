import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { calculateTco } from '@shared/calculator';
import { VEHICLE_DETAILS } from '@shared/data/vehicleCatalog';
import type {
  CalculationResponsePayload,
  CostBreakdown,
  CostOverrides,
  PurchaseMethod,
  ScenarioKey,
} from '@shared/types/tco.types';

interface SnapshotCase {
  results: Record<PurchaseMethod, Record<string, Record<string, CalculationResponsePayload>>>;
  overrides: Record<string, CostOverrides>;
}

interface SnapshotPayload {
  cases: Record<string, SnapshotCase>;
}

const BREAKDOWN_FIELDS: Array<keyof CostBreakdown> = [
  'purchase_cost',
  'fuel_cost',
  'maintenance_cost',
  'insurance_cost',
  'registration_cost',
  'battery_replacement_cost',
  'financing_cost',
  'carbon_cost',
  'charging_labour_cost',
  'payload_penalty_cost',
  'residual_value',
  'depreciation',
  'taxes_and_fees',
];

const KEY_FIELDS: Array<keyof CalculationResponsePayload> = ['total_cost', 'annual_cost', 'cost_per_km'];
const PURCHASE_METHODS: PurchaseMethod[] = ['financed', 'outright'];
const SCENARIO_KEYS: ScenarioKey[] = ['baseline', 'technology_breakthrough', 'oil_crisis'];
const RELATIVE_TOLERANCE = 0.01;
const ABSOLUTE_TOLERANCE = 1e-6;

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(currentDir, '../../../../..');
const venvPython = path.join(repoRoot, '.venv', 'bin', 'python');
const pythonExecutable = fs.existsSync(venvPython) ? venvPython : 'python3';

const rawSnapshot = execSync(
  `${pythonExecutable} scripts/export_tco_snapshot.py`,
  { cwd: repoRoot, encoding: 'utf-8' }
);
const SNAPSHOT = JSON.parse(rawSnapshot) as SnapshotPayload;

const expectClose = (actual: number, expected: number, label: string) => {
  const absoluteDiff = Math.abs(actual - expected);
  if (Math.abs(expected) < ABSOLUTE_TOLERANCE) {
    if (absoluteDiff > ABSOLUTE_TOLERANCE) {
      throw new Error(`${label}: Δ=${absoluteDiff} exceeds absolute tolerance ${ABSOLUTE_TOLERANCE}`);
    }
    return;
  }
  const relativeDiff = absoluteDiff / Math.abs(expected);
  if (relativeDiff > RELATIVE_TOLERANCE) {
    throw new Error(`${label}: relative Δ=${relativeDiff} exceeds tolerance ${RELATIVE_TOLERANCE}`);
  }
};

describe('TypeScript TCO calculator parity', () => {
  for (const [caseName, caseData] of Object.entries(SNAPSHOT.cases)) {
    describe(`override case: ${caseName}`, () => {
      for (const purchaseMethod of PURCHASE_METHODS) {
        describe(`purchase method: ${purchaseMethod}`, () => {
          for (const scenarioKey of SCENARIO_KEYS) {
            it(`matches Python for scenario ${scenarioKey}`, () => {
              const scenarioResults = caseData.results[purchaseMethod][scenarioKey];
              expect(scenarioResults).toBeDefined();

              VEHICLE_DETAILS.forEach((vehicle) => {
                const pythonResult = scenarioResults[vehicle.vehicle_id];
                expect(pythonResult).toBeDefined();
                const overrides = caseData.overrides[vehicle.vehicle_id];

                const tsResult = calculateTco({
                  vehicle_id: vehicle.vehicle_id,
                  scenario_name: scenarioKey,
                  purchase_method: purchaseMethod,
                  overrides,
                });

                KEY_FIELDS.forEach((field) => {
                  expectClose(
                    tsResult[field] as number,
                    pythonResult[field] as number,
                    `${vehicle.vehicle_id}:${field}`
                  );
                });

                BREAKDOWN_FIELDS.forEach((field) => {
                  expectClose(
                    tsResult.breakdown[field],
                    pythonResult.breakdown[field],
                    `${vehicle.vehicle_id}:breakdown.${field}`
                  );
                });

                expect(tsResult.scenario_name).toBe(pythonResult.scenario_name);
              });
            });
          }
        });
      }
    });
  }
});
