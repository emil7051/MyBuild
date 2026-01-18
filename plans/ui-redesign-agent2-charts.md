# Agent 2: Charts & Data Visualization

## Context
You are one of three Opus 4.5 sub-agents working in parallel on a UI/UX redesign of the MyBuild TCO Calculator. This is a React/TypeScript app using Recharts for data visualization.

**Your focus**: All chart components - updating colors and creating 3 new visualizations
**Other agents (DO NOT TOUCH THEIR FILES):**
- Agent 1: Config files, CSS, shared components (Card, Button, Field, Select, AppShell, WizardStepper)
- Agent 3: Copy changes in wizard step components

## Brand Color Palette for Charts
- **Diesel vehicles**: `#EA5300` (Burnt Orange)
- **Electric vehicles**: `#00FFC7` (Ion Aqua)
- **Winner highlight**: `#FFC700` (Nova Yellow) with black stroke
- **Grid lines**: `#E5E5E5` (brand border)
- **Axis text**: `#000000` (black)

**Cost breakdown palette (11 categories):**
```typescript
const COST_COLORS = {
  purchase_cost: '#3040B9',      // Electric Blue dark
  fuel_cost: '#3B52FF',          // Electric Blue main
  maintenance_cost: '#7080FF',   // Electric Blue mid
  insurance_cost: '#B9C2FF',     // Electric Blue light
  registration_cost: '#844A34',  // Burnt Orange dark
  battery_replacement_cost: '#005A46',  // Ion Aqua dark
  financing_cost: '#EA5300',     // Burnt Orange main
  carbon_cost: '#F2AE95',        // Burnt Orange light
  charging_labour_cost: '#00FFC7',      // Ion Aqua main
  payload_penalty_cost: '#C5FFF3',      // Ion Aqua light
  taxes_and_fees: '#000000',     // Black
};
```

## CRITICAL: Do NOT Modify
- Any files in `frontend/src/state/`
- Any files in `frontend/src/hooks/`
- Any files in `frontend/src/services/calculator/`
- `frontend/src/utils/payload.ts`
- Calculation logic in any file

## Data Structure Reference
Results come from `useTCOStore` with this shape:
```typescript
interface CalculationResponsePayload {
  vehicle_id: string;
  vehicle_name: string;
  drivetrain_type: 'Diesel' | 'BEV';
  results: {
    total_lifetime_cost_pv: number;
    annual_cost_year_1: number;
    cost_per_km: number;
    // Cost breakdown components:
    purchase_cost_pv: number;
    fuel_cost_pv: number;
    maintenance_cost_pv: number;
    // ... etc
  };
}
```

---

## Your Files to Modify/Create

### 1. frontend/src/components/results/CostPerKmChart.tsx (MODIFY)
**Current issues**: Uses off-brand `#124df0` blue for all bars
**Changes:**
- Import `Cell` from recharts for per-bar coloring
- Color bars by vehicle type:
  - Diesel: `#EA5300` (Burnt Orange)
  - Electric: `#00FFC7` (Ion Aqua)
  - Winner: `#FFC700` (Nova Yellow) with `stroke="#000000"` `strokeWidth={2}`
- Add `radius={[6, 6, 0, 0]}` for rounded bar tops
- Update tooltip styling with brand fonts and colors
- Update CartesianGrid: `stroke="#E5E5E5"` `vertical={false}`

```tsx
// Color utility
const getBarColor = (drivetrainType: string, isWinner: boolean) => {
  if (isWinner) return '#FFC700';
  return drivetrainType === 'Diesel' ? '#EA5300' : '#00FFC7';
};
```

### 2. frontend/src/components/results/CostBreakdownChart.tsx (MODIFY)
**Current issues**: Uses random blues/teals not from brand palette
**Changes:**
- Replace color array with brand-aligned palette (see COST_COLORS above)
- Update tooltip with sorted values (highest first) and percentages
- Add custom legend component with better styling
- Add `radius={[4, 4, 0, 0]}` for subtle rounded corners

### 3. frontend/src/components/results/PaybackChart.tsx (CREATE)
**Purpose**: "When does the EV break even?"
Line chart showing cumulative costs over time with crossover point.

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';
import { Card } from '../shared/Card';

interface PaybackChartProps {
  dieselResult: CalculationResponsePayload;
  bevResult: CalculationResponsePayload;
  horizonYears?: number; // default 15
}

// Generate year-by-year cumulative costs
// Find crossover point (payback year)
// Show yellow vertical ReferenceLine at payback with label
// Diesel line: #EA5300, BEV line: #00FFC7
// Card title: "Payback timeline"
// Card subtitle: "When does switching to electric break even?"
```

### 4. frontend/src/components/results/SavingsWaterfallChart.tsx (CREATE)
**Purpose**: "Where do the savings come from?"
Waterfall chart showing how savings accumulate from different categories.

```tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../shared/Card';

interface WaterfallChartProps {
  dieselResult: CalculationResponsePayload;
  bevResult: CalculationResponsePayload;
}

// Data structure for waterfall:
// { name: 'Diesel TCO', value: totalDiesel, fill: '#EA5300', isTotal: true }
// { name: 'Fuel savings', value: -fuelSavings, fill: '#00FFC7' } // negative = savings
// { name: 'Maintenance savings', value: -maintSavings, fill: '#00FFC7' }
// { name: 'Higher purchase cost', value: purchaseDelta, fill: '#EA5300' } // positive = cost
// { name: 'Electric TCO', value: totalBEV, fill: '#3B52FF', isTotal: true }

// Card title: "Savings breakdown"
// Card subtitle: "What drives the cost difference?"
```

### 5. frontend/src/components/results/SensitivityTornadoChart.tsx (CREATE)
**Purpose**: "Which assumptions matter most?"
Horizontal bar chart showing impact of +/- 20% variation in key inputs.

```tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { Card } from '../shared/Card';

interface SensitivityChartProps {
  baseComparison: { diesel: CalculationResponsePayload; bev: CalculationResponsePayload };
  // Would need to run sensitivity calculations or estimate impact
}

// Data structure:
// { factor: 'Diesel price', low: -15000, high: 18000 }
// { factor: 'Electricity price', low: -8000, high: 10000 }
// { factor: 'Annual kms', low: -12000, high: 14000 }
// { factor: 'Battery life', low: -5000, high: 3000 }

// Horizontal bars extending left (low/#EA5300) and right (high/#00FFC7)
// ReferenceLine at x=0
// Card title: "Sensitivity analysis"
// Card subtitle: "How do assumptions affect the comparison?"
```

### 6. frontend/src/components/results/ResultsPanel.tsx (MODIFY)
**Changes:**
- Import and integrate new chart components
- Add section below existing charts:
```tsx
{/* New Analysis Section */}
<div className="mt-8 space-y-6">
  <h3 className="text-xl font-heading-minor">Deeper Analysis</h3>
  <div className="grid gap-6 lg:grid-cols-2">
    <PaybackChart dieselResult={dieselResult} bevResult={bestBevResult} />
    <SensitivityTornadoChart baseComparison={{ diesel: dieselResult, bev: bestBevResult }} />
  </div>
  <SavingsWaterfallChart dieselResult={dieselResult} bevResult={bestBevResult} />
</div>
```
- Also update copy: "Lifetime PV" → "Total cost" throughout

---

## Empty/Loading States
Add these to new charts:

```tsx
// Loading
<div className="flex items-center justify-center h-80 bg-slate-50">
  <div className="w-10 h-10 border-4 border-brand-primary border-t-transparent rounded-full animate-spin" />
</div>

// Empty (e.g., only diesel selected, no BEV to compare)
<div className="flex flex-col items-center justify-center h-80 bg-slate-50 border-2 border-dashed border-slate-200">
  <p className="text-sm text-slate-500">Select an electric truck to see this analysis</p>
</div>
```

---

## Testing Checklist
1. Colors are correct and accessible (sufficient contrast)
2. Winner is clearly highlighted in yellow
3. Diesel vs Electric clearly distinguishable
4. Tooltips show useful information
5. New charts render without errors
6. Empty states show when data unavailable
7. Run `bun test` to ensure no regressions
