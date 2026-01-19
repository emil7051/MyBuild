/**
 * Script to regenerate verification_data.json from the TypeScript calculator.
 * 
 * Run with: cd frontend && bunx tsx ../scripts/regenerate_verification_data.ts
 */

import { calculateTco } from '../shared/calculator';
import type { CalculationRequestPayload } from '../shared/types/tco.types';
import * as fs from 'fs';
import * as path from 'path';

interface VerificationCase {
  id: string;
  input: CalculationRequestPayload;
  expected: ReturnType<typeof calculateTco>;
}

// Define all test cases to regenerate
const testCases: Array<{ id: string; input: CalculationRequestPayload }> = [
  // BEV001 - Light Rigid
  { id: 'BEV001-baseline-financed', input: { vehicle_id: 'BEV001', scenario_name: 'baseline', purchase_method: 'financed', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  { id: 'BEV001-baseline-outright', input: { vehicle_id: 'BEV001', scenario_name: 'baseline', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  // BEV002 - Medium Rigid
  { id: 'BEV002-baseline-financed', input: { vehicle_id: 'BEV002', scenario_name: 'baseline', purchase_method: 'financed', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  { id: 'BEV002-baseline-outright', input: { vehicle_id: 'BEV002', scenario_name: 'baseline', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  // DSL001 - Light Rigid Diesel
  { id: 'DSL001-baseline-financed', input: { vehicle_id: 'DSL001', scenario_name: 'baseline', purchase_method: 'financed', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  { id: 'DSL001-baseline-outright', input: { vehicle_id: 'DSL001', scenario_name: 'baseline', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  // DSL002 - Medium Rigid Diesel
  { id: 'DSL002-baseline-financed', input: { vehicle_id: 'DSL002', scenario_name: 'baseline', purchase_method: 'financed', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  { id: 'DSL002-baseline-outright', input: { vehicle_id: 'DSL002', scenario_name: 'baseline', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  // Scenario variations
  { id: 'BEV001-technology_breakthrough-outright', input: { vehicle_id: 'BEV001', scenario_name: 'technology_breakthrough', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
  { id: 'DSL001-oil_crisis-outright', input: { vehicle_id: 'DSL001', scenario_name: 'oil_crisis', purchase_method: 'outright', duty_cycle: { urban: 60, regional: 25, longHaul: 15 } } },
];

function main() {
  const results: VerificationCase[] = testCases.map(({ id, input }) => {
    const result = calculateTco(input);
    return {
      id,
      input: {
        vehicle_id: input.vehicle_id,
        scenario_name: input.scenario_name,
        purchase_method: input.purchase_method,
        overrides: input.overrides ?? null,
        vehicle_overrides: input.vehicle_overrides ?? null,
      } as CalculationRequestPayload,
      expected: result,
    };
  });

  const outputPath = path.join(__dirname, '../shared/calculator/verification_data.json');
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(`Generated ${results.length} verification cases to ${outputPath}`);
}

main();
