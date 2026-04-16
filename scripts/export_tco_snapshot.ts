/**
 * Regenerate verification_data.json by running the TCO calculator
 * for all test cases and writing the results.
 *
 * Usage: npx tsx scripts/export_tco_snapshot.ts
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Register path aliases for shared imports
import { register } from 'node:module';

const REPO_ROOT = resolve(new URL('.', import.meta.url).pathname, '..');
const FIXTURE_PATH = resolve(REPO_ROOT, 'shared/calculator/verification_data.json');

// We need to import the calculator dynamically after setup
async function main() {
  // Read existing fixture to get the test case inputs
  const existingData = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));

  // Dynamic import of calculator (works with tsx)
  const { calculateTco } = await import('../shared/calculator/tcoCalculator.js');

  const updatedData = existingData.map((testCase: { id: string; input: Record<string, unknown> }) => {
    const input = {
      vehicle_id: testCase.input.vehicle_id as string,
      scenario_name: testCase.input.scenario_name as string,
      purchase_method: testCase.input.purchase_method as string,
      ...(testCase.input.overrides ? { overrides: testCase.input.overrides } : {}),
      ...(testCase.input.vehicle_overrides ? { vehicle_overrides: testCase.input.vehicle_overrides } : {}),
      ...(testCase.input.duty_cycle ? { duty_cycle: testCase.input.duty_cycle } : {}),
    };

    try {
      const result = calculateTco(input as Parameters<typeof calculateTco>[0]);
      return {
        id: testCase.id,
        input: testCase.input,
        expected: result,
      };
    } catch (error) {
      console.error(`Failed for ${testCase.id}:`, error);
      return testCase; // keep original on failure
    }
  });

  writeFileSync(FIXTURE_PATH, JSON.stringify(updatedData, null, 2) + '\n');
  console.log(`Updated ${updatedData.length} test cases in verification_data.json`);
}

main().catch(console.error);
