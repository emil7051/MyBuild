# Guided UX Redesign: Phased Implementation Plan

## Purpose

This plan translates [`docs/UX-thinking.md`](./UX-thinking.md) into an execution roadmap that can be delivered safely in increments. It contains everything a developer needs to implement each phase without cross-referencing the design doc.

**Primary goal:** Help low-finance subcontractors and drivers get to a trustworthy answer fast, then opt into deeper configuration.

**Target user:** A sub-contractor or owner-driver who knows their truck by make and model, thinks in "km per day" and "dollars per week on diesel", and wants an answer ("will I save money?") before they invest effort in configuration.

## Design Principles (from UX-thinking.md)

1. **Answer first, configure later.** Show a headline result within 2-3 clicks.
2. **Plain language.** "How far do you drive each day?" not "Annual kilometres."
3. **Smart defaults over empty forms.** If we can infer it, don't ask for it.
4. **Progressive disclosure.** Spec overrides and scenario modelling live behind "Fine-tune".
5. **One recommendation, not a comparison grid.** Suggest the single best electric match. Let power users add more.

## Success Criteria

- Time to first headline result: under 60 seconds for first-time users.
- Clicks to first headline result:
  - Path A (owns truck): 2-4 clicks.
  - Path B (buying): 2-3 clicks.
  - Path B ("Not sure"): 1 click.
  - Current wizard baseline: 6+ clicks.
- Completion rate to headline result improves versus current wizard baseline.
- Advanced panel open rate indicates progressive disclosure is working (users are not blocked by complexity).
- No regression in calculator parity or result correctness.

## Vehicle Catalog Context

The catalog has **16 vehicles** (8 BEV, 8 Diesel) across 3 weight classes. Every vehicle has a `comparison_pair` linking it to its diesel/BEV counterpart. This is the backbone of the auto-recommendation.

| Weight Class | Diesel Models | BEV Models |
|---|---|---|
| Light Rigid | Hino 300, Hyundai Mighty, Hino 500 | Jac N75, Hyundai Mighty Electric, Jac N90 |
| Medium Rigid | Volvo FE, MB Actros | Volvo FL, MB eActros 300 |
| Articulated | MB Actros, Volvo FH, Scania R560 | MB eActros 600, Volvo FH, Scania 45R |

## Screen Flow Overview

```
                    +-------------+
                    |  Landing    |
                    |  "Do you    |
                    |  have a     |
                    |  truck?"    |
                    +------+------+
                           |
              +------------+------------+
              |                         |
     +--------v--------+     +----------v--------+
     |  PATH A          |     |  PATH B            |
     |  Pick size       |     |  Pick work type    |
     |  Pick model      |     |                    |
     +--------+---------+     +----------+---------+
              |                          |
     +--------v---------+     +----------v---------+
     |  Daily kms +      |     |  Daily kms          |
     |  driving pattern  |     |  (pre-filled)       |
     +--------+----------+     +----------+----------+
              |                           |
              +-----------+---------------+
                          |
                 +--------v--------+
                 |  HEADLINE       |
                 |  RESULT         |
                 |                 |
                 |  "Save $47k     |
                 |   over 15 yrs"  |
                 +--------+--------+
                          |
            +-------------+-------------+
            |                           |
   +--------v---------+     +-----------v--------+
   |  Full Breakdown   |     |  Fine-Tune          |
   |  (charts)         |     |  (config panel)     |
   |                   |     |                     |
   |  Cost per km      |     |  Scenarios           |
   |  Components       |     |  Duty cycle          |
   |  Payback          |     |  Cost adjustments    |
   |  Sensitivity      |     |  Vehicle specs       |
   +-------------------+     |  Add more trucks     |
                             +---------------------+
```

## Delivery Strategy

- Keep existing calculator engine, results components, and state shape.
- Add a guided entry layer as a new route, not a rewrite.
- Use feature flag to run current wizard and guided flow in parallel until confidence is high.
- Track behavioural metrics from day one.

---

## Phase 0: Foundation and Guardrails

### Objective

Set up architecture, flags, and data contracts to support the guided flow without breaking existing behaviour.

### User Stories Addressed

- **Story 9: Work-Type Profile Data** (full delivery)

### Scope

#### 0.1 Feature Flag

Add a feature flag to toggle between current wizard and guided flow. Both routes coexist. Default: current wizard.

**Implementation:** A simple boolean in app config or environment variable. Route-level: `/compare` (current wizard) vs `/guided` (new flow), with the flag controlling which is the default landing route.

#### 0.2 Work-Type Profiles Data

Create `WORK_TYPE_PROFILES` in the shared data layer. This is the mapping that powers Path B and the driving pattern radio buttons in Path A.

```typescript
// shared/data/workTypeProfiles.ts

export type WorkTypeKey = 'local_delivery' | 'regional_freight' | 'interstate' | 'mixed';

export interface WorkTypeProfile {
  label: string;
  description: string;
  recommended_weight_class: string | null; // null = show all
  default_daily_km: number;
  duty_cycle: { urban: number; regional: number; longHaul: number };
}

export const WORK_TYPE_PROFILES: Record<WorkTypeKey, WorkTypeProfile> = {
  local_delivery: {
    label: 'Local deliveries',
    description: 'Food, parcels, furniture, retail',
    recommended_weight_class: 'Light Rigid',
    default_daily_km: 100,
    duty_cycle: { urban: 80, regional: 15, longHaul: 5 },
  },
  regional_freight: {
    label: 'Regional freight',
    description: 'Between cities within a state',
    recommended_weight_class: 'Medium Rigid',
    default_daily_km: 200,
    duty_cycle: { urban: 15, regional: 60, longHaul: 25 },
  },
  interstate: {
    label: 'Interstate / long haul',
    description: 'Capital to capital, cross-state',
    recommended_weight_class: 'Articulated',
    default_daily_km: 350,
    duty_cycle: { urban: 5, regional: 15, longHaul: 80 },
  },
  mixed: {
    label: 'Mixed / not sure',
    description: 'Show me all the options',
    recommended_weight_class: null,
    default_daily_km: 150,
    duty_cycle: { urban: 50, regional: 35, longHaul: 15 },
  },
} as const;

export const WORKING_DAYS_PER_YEAR = 240;
```

**Decision:** Manually maintained (not generated from Python) since this is a UX mapping layer, not a calculator input. Document this clearly in the file header.

#### 0.3 Guided Flow State Additions

Extend the UI state (companion to `WizardData`, not replacing it) to track the guided flow's selections:

```typescript
// Additions to tcoStore or a separate guided flow slice

interface GuidedFlowState {
  entryPath: 'has_truck' | 'looking_to_buy' | null;
  selectedWeightClass: string | null;        // Path A: from size card
  selectedWorkType: WorkTypeKey | null;       // Path B: from work type card
  dailyKm: number | null;                    // Plain-language input
  drivingPattern: WorkTypeKey | null;         // Path A: radio selection
  showFullBreakdown: boolean;                 // Expansion toggle
  showFineTune: boolean;                     // Expansion toggle
}
```

These values are translated into the existing `WizardData` shape before calculations run. The calculator never sees `dailyKm` or `drivingPattern` directly.

**State persistence:** Version the persisted state and provide migration defaults so existing localStorage data isn't corrupted.

#### 0.4 Telemetry Event Schema

Define event names and payloads for funnel tracking:

| Event | Payload | Trigger |
|---|---|---|
| `guided.entry_viewed` | `{}` | Landing fork renders |
| `guided.path_selected` | `{ path: 'has_truck' \| 'looking_to_buy' }` | User clicks entry card |
| `guided.truck_size_selected` | `{ weight_class: string }` | Path A size card click |
| `guided.model_selected` | `{ vehicle_id: string }` | Path A model dropdown |
| `guided.work_type_selected` | `{ work_type: WorkTypeKey }` | Path B work type card |
| `guided.daily_km_changed` | `{ daily_km: number, annual_km: number }` | km input change (debounced) |
| `guided.driving_pattern_selected` | `{ pattern: WorkTypeKey }` | Path A radio click |
| `guided.result_rendered` | `{ diesel_id: string, bev_id: string, savings: number }` | Headline result displays |
| `guided.full_breakdown_opened` | `{}` | User expands charts |
| `guided.fine_tune_opened` | `{}` | User expands config panel |
| `guided.comparison_added` | `{ vehicle_id: string }` | User adds a truck in fine-tune |

**Implementation:** Create a `frontend/src/services/guidedTelemetry.ts` with typed event emitters. Wire into existing analytics infrastructure (or stub for now).

### Implementation Targets

| File | Action |
|---|---|
| `shared/data/workTypeProfiles.ts` | **New.** Profiles, types, and `WORKING_DAYS_PER_YEAR` constant. |
| `shared/types/tco.types.ts` | Extend with `WorkTypeProfile` and `WorkTypeKey` exports (or re-export from profiles file). |
| `frontend/src/state/tcoStore.ts` | Add `GuidedFlowState` slice alongside existing `WizardData`. Version persisted state. |
| `frontend/src/services/guidedTelemetry.ts` | **New.** Typed event emitters for guided flow funnel. |
| `frontend/src/config.ts` or equivalent | Add `FEATURE_GUIDED_FLOW` flag. |
| Router config | Add `/guided` route (inactive by default). |

### Acceptance Criteria

- App can toggle between current wizard and guided flow via feature flag.
- Type-safe `WORK_TYPE_PROFILES` exists and is importable by frontend.
- `GuidedFlowState` is persisted with version migration.
- Telemetry events are typed, documented, and emit (even if to console in dev).
- All existing tests pass. No changes to calculator or results components.

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| State shape churn creates migration issues in persisted storage | Version persisted state. Migration function provides defaults for new fields. |
| Telemetry schema drift | Types enforce event payloads at compile time. |

---

## Phase 1: MVP Guided Entry + Instant Headline Result

### Objective

Deliver the shortest path to value: a user picks their situation and sees a savings headline without touching advanced configuration.

### User Stories Addressed

- **Story 1: Entry Point Fork** (full delivery)
- **Story 2: Truck Identification, Path A** (full delivery)
- **Story 3: Usage Profile, Path A** (full delivery)
- **Story 4: Work Type Selection, Path B** (full delivery)
- **Story 5: Instant Headline Result** (full delivery)

### Scope

#### 1.1 Entry Fork (`EntryForkCards`)

The landing screen. Two large, tappable cards. No dropdowns, no forms, no other chrome.

```
+-----------------------------+  +-----------------------------+
|                             |  |                             |
|      I have a truck         |  |      I'm looking to buy     |
|                             |  |                             |
|  "I drive a diesel truck    |  |  "I'm researching my first  |
|   and want to see if        |  |   truck or planning an      |
|   electric makes sense"     |  |   upgrade"                  |
|                             |  |                             |
+-----------------------------+  +-----------------------------+
```

**Behaviour:**
- On click, sets `entryPath` in guided state and scrolls/transitions to the next section.
- No page navigation. The entire guided flow lives on a single scrolling page.
- Mobile: cards stack vertically.
- Cards have hover/focus states and are keyboard-navigable.

#### 1.2 Truck Size Cards (`TruckSizeCards`) (Path A only)

Three visual cards for weight class, using plain language as primary labels. Technical weight class as subtle subtitle.

```
What kind of truck do you drive?

+--------------+  +--------------+  +--------------+
|  [image]     |  |  [image]     |  |  [image]     |
|              |  |              |  |              |
|  Small truck |  |  Medium      |  |  Semi /      |
|  (rigid)     |  |  truck       |  |  prime mover |
|              |  |  (rigid)     |  |              |
|  Up to ~6t   |  |  ~10-25t     |  |  B-double /  |
|  payload     |  |  payload     |  |  road train  |
|              |  |              |  |              |
|  Hino 300,   |  |  Volvo FE,   |  |  Actros,     |
|  Hyundai     |  |  Actros      |  |  Volvo FH,   |
|  Mighty      |  |              |  |  Scania      |
+--------------+  +--------------+  +--------------+
```

**Card data mapping:**

| Card Label | Subtitle | Weight Class Filter | Payload Hint | Example Models |
|---|---|---|---|---|
| Small truck (rigid) | Light Rigid | `Light Rigid` | Up to ~6t | Hino 300, Hyundai Mighty, Hino 500 |
| Medium truck (rigid) | Medium Rigid | `Medium Rigid` | ~10-25t | Volvo FE, MB Actros |
| Semi / prime mover | Articulated | `Articulated` | B-double / road train | MB Actros, Volvo FH, Scania R560 |

**Behaviour:**
- Selected card gets highlighted border/ring. Other cards dim slightly.
- On selection, a model dropdown appears inline below the cards (not a new page).
- Changing size card clears model selection and resets the dropdown.
- Example model names on each card are pulled from the vehicle catalog, filtered by `weight_class` and `drivetrain_type === 'Diesel'`.

#### 1.3 Model Dropdown (Path A, inline after size card)

A short dropdown scoped to the selected weight class, showing only diesel models.

```
Which model is closest to yours?

  Hino 300         ~4.5t payload, ~$80k
  Hyundai Mighty   ~4t payload, ~$75k
  Hino 500         ~6t payload, ~$130k
```

**Behaviour:**
- Each option shows: `model_name`, `~{payload}t payload`, `~${msrp formatted}`.
- Below the dropdown: "Don't see your truck? Pick the closest match by payload. You can adjust the specs later."
- On selection:
  - Sets `currentVehicle` in `WizardData` store.
  - Auto-selects the vehicle's `comparison_pair` BEV into `comparisonVehicles`.
  - Pre-fills `dailyKm` from `annual_kms / WORKING_DAYS_PER_YEAR` (rounded).
  - Triggers telemetry: `guided.model_selected`.

#### 1.4 Usage Profile (`DailyKmInput` + `DrivingPatternRadio`) (Path A, inline)

Appears below the model dropdown after a model is selected.

```
Roughly how far do you drive on a typical day?
+--------------------------------------+
|  [  150  ] km/day                    |
|  That's about 36,000 km/year         |
+--------------------------------------+

What kind of driving do you mostly do?
  * Mostly city / metro deliveries
  * Mix of city and regional
  * Mostly regional / inter-city
  * Long haul / interstate
```

**DailyKmInput spec:**
- Number input, `min=10`, `max=1500`, `step=10`.
- Live conversion displayed below: `That's about {dailyKm * WORKING_DAYS_PER_YEAR} km/year`.
- Pre-filled with catalog default for selected vehicle, converted to daily.
- On change (debounced 300ms): updates `overrides.annual_kms_variation` in store by computing `dailyKm * 240` and converting to the appropriate override. Or simpler: store the raw annual kms value.

**DrivingPatternRadio spec:**
- Four radio buttons. Labels are plain language (no percentages shown).
- Default selection: "Mix of city and regional".
- Mapping uses `WORK_TYPE_PROFILES` duty cycle values:

| Radio Label | Duty Cycle (urban/regional/longHaul) |
|---|---|
| Mostly city / metro deliveries | 80 / 15 / 5 |
| Mix of city and regional | 50 / 35 / 15 |
| Mostly regional / inter-city | 15 / 60 / 25 |
| Long haul / interstate | 5 / 15 / 80 |

- On change: updates `dutyCycle` in `WizardData` store.

**Optional skip:** Both inputs have sensible defaults. The headline result can auto-calculate as soon as a model is selected, using defaults. The usage profile section refines the result but doesn't gate it.

#### 1.5 Work Type Cards (`WorkTypeCards`) (Path B only)

Four visual cards. Appears after the user selects "I'm looking to buy" in the entry fork.

```
What kind of trucking will you do?

+--------------+  +--------------+  +--------------+  +--------------+
|              |  |              |  |              |  |              |
|  Local       |  |  Regional    |  |  Interstate  |  |  I'm not     |
|  deliveries  |  |  freight     |  |  / long haul |  |  sure yet    |
|              |  |              |  |              |  |              |
|  Food,parcels|  |  Between     |  |  Capital to  |  |  Show me     |
|  furniture,  |  |  cities      |  |  capital,    |  |  all the     |
|  retail      |  |  within a    |  |  cross-state |  |  options     |
|              |  |  state       |  |              |  |              |
+--------------+  +--------------+  +--------------+  +--------------+
```

**Behaviour:**
- On selection, the profile from `WORK_TYPE_PROFILES` sets:
  - `selectedWorkType` in guided state.
  - `dutyCycle` in `WizardData` from the profile.
  - `dailyKm` in guided state from `default_daily_km`.
  - Annual kms computed and stored.
  - `currentVehicle` and `comparisonVehicles` auto-selected: pick the first `comparison_pair` from the recommended weight class. For "Not sure" (`null` weight class), pick one representative pair per weight class.
- DailyKmInput appears below (pre-filled, editable).
- For "Not sure": the headline result section shows a tabbed or stacked view with one comparison per weight class.

**Vehicle auto-selection logic for Path B:**

```typescript
function selectDefaultVehicles(weightClass: string | null, catalog: VehicleDetail[]) {
  if (weightClass) {
    // Pick the first diesel in this weight class
    const diesel = catalog.find(v => v.weight_class === weightClass && v.drivetrain_type === 'Diesel');
    const bev = diesel ? catalog.find(v => v.vehicle_id === diesel.comparison_pair) : null;
    return { currentVehicle: diesel?.vehicle_id, comparisonVehicles: bev ? [bev.vehicle_id] : [] };
  }
  // "Not sure": pick first diesel+BEV pair per weight class
  const weightClasses = ['Light Rigid', 'Medium Rigid', 'Articulated'];
  return weightClasses.map(wc => {
    const diesel = catalog.find(v => v.weight_class === wc && v.drivetrain_type === 'Diesel');
    const bev = diesel ? catalog.find(v => v.vehicle_id === diesel.comparison_pair) : null;
    return { diesel, bev };
  });
}
```

#### 1.6 Headline Result (`HeadlineResult`)

The payoff. Appears inline below the selection inputs as soon as a valid diesel + BEV pair exists in the store. No button click required.

**When electric saves money:**

```
+-------------------------------------------------------------+
|                                                             |
|  Your truck: Hino 300 (Diesel)                              |
|  Electric match: Jac N75                                    |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                                                       |  |
|  |   Electric could save you                             |  |
|  |                                                       |  |
|  |        $47,000                                        |  |
|  |     over 15 years                                     |  |
|  |                                                       |  |
|  |   That's about $3,100 per year                        |  |
|  |   or $0.14 less per kilometre                         |  |
|  |                                                       |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  +-------------+  +-------------+                          |
|  | Diesel      |  | Electric    |                          |
|  | $X.XX / km  |  | $X.XX / km  |                          |
|  | $XXX,XXX    |  | $XXX,XXX    |                          |
|  | total       |  | total       |                          |
|  +-------------+  +-------------+                          |
|                                                             |
|  [See full breakdown]     [Fine-tune assumptions]           |
|                                                             |
+-------------------------------------------------------------+
```

**When diesel is cheaper:**

```
|  Based on these assumptions, diesel costs less              |
|  over 15 years (~$XX,XXX difference).                       |
|                                                             |
|  But that could change. Try a different scenario to see     |
|  how fuel prices or technology shifts affect the numbers.   |
|  [Explore scenarios]                                        |
```

**Data source:**
- Reads from `results` in the Zustand store (same `CalculationResponsePayload` the existing charts use).
- Headline values derived from:
  - `total_cost` delta between diesel and BEV results.
  - `cost_per_km` delta.
  - Annual savings = total delta / 15 years.

**Behaviour:**
- Calculation triggers via existing `useCalculations` hook as soon as a valid `ComparisonRequestPayload` can be built.
- Loading state: spinner card with "Crunching the numbers..."
- Two expansion buttons at the bottom (collapsed by default, expanded in Phase 2).
- On render: emit `guided.result_rendered` telemetry with savings figure.

**Path B "Not sure" variant:** Show three headline cards (one per weight class), each with diesel vs BEV comparison. User can tap into any one for the full breakdown.

### Implementation Targets

| File | Action |
|---|---|
| `frontend/src/pages/GuidedFlowPage.tsx` | **New.** Single-page guided flow, conditionally routed via feature flag. |
| `frontend/src/components/guided/EntryForkCards.tsx` | **New.** Two-card landing fork. |
| `frontend/src/components/guided/TruckSizeCards.tsx` | **New.** Three weight-class cards with inline model dropdown. |
| `frontend/src/components/guided/WorkTypeCards.tsx` | **New.** Four work-type cards for Path B. |
| `frontend/src/components/guided/DailyKmInput.tsx` | **New.** Number input with live annual conversion. |
| `frontend/src/components/guided/DrivingPatternRadio.tsx` | **New.** Four radio buttons mapping to duty cycle presets. |
| `frontend/src/components/guided/HeadlineResult.tsx` | **New.** Savings headline with diesel vs electric summary cards. |
| `frontend/src/hooks/useGuidedFlow.ts` | **New.** Hook to translate guided state into `WizardData` and trigger calculations. |
| `frontend/src/hooks/useCalculations.ts` | No changes. Reused as-is. |
| `frontend/src/utils/payload.ts` | Minor: ensure `buildComparisonPayload` works with guided-flow-populated store state. |

### Acceptance Criteria

- User can reach a headline savings result without navigating through a stepper.
- No multipliers, duty cycle percentages, or spec inputs are required to reach first result.
- Path A: select size card + model dropdown = headline result (with defaults). Usage inputs refine.
- Path B: select work type card = headline result (with defaults). Daily km input refines.
- Both paths produce valid `ComparisonRequestPayload` objects and render correct results.
- If no valid payload can be built (e.g., no models in a weight class), UI shows a plain-language next action.
- Existing wizard route (`/compare`) still works unchanged.
- All existing calculator parity tests pass.

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Path B inferred defaults may feel too generic | Show "based on typical profile for [work type]" note. Keep daily km editable. Link to fine-tune. |
| Auto-selected comparison pair may not be the best match | Use `comparison_pair` from catalog (curated). Note: "This is the closest electric match we have data for." |
| Single-page scroll may feel long on mobile | Progressive reveal: each section only appears after the previous is answered. Smooth scroll-to on new section. |

---

## Phase 2: Progressive Disclosure and Plain Language Conversion

### Objective

Wire up the "See full breakdown" and "Fine-tune assumptions" expansion panels, and convert the confusing multiplier inputs to percentage-based display.

### User Stories Addressed

- **Story 6: Full Breakdown (Expandable)** (full delivery)
- **Story 7: Fine-Tune Panel (Expandable)** (full delivery)
- **Story 8: Multiplier-to-Percentage Translation** (full delivery)

### Scope

#### 2.1 Full Breakdown Expansion

The "See full breakdown" button on the HeadlineResult toggles visibility of the existing chart suite.

**Behaviour:**
- On click: sets `showFullBreakdown = true` in guided state, smooth-scrolls to chart section.
- Charts rendered: reuse existing `ResultsPanel` components (cost per km, cost components, payback timeline, savings waterfall, sensitivity tornado).
- All charts receive data from the same `results` store that HeadlineResult reads.
- Section is collapsible (toggle back to hidden).
- Charts are lazy-loaded (existing `React.lazy` / `Suspense` wrapping stays).
- On mobile: charts stack full-width.
- Emit `guided.full_breakdown_opened` telemetry on first expand.

**No new chart logic.** This is purely a layout/visibility change. The existing chart components render exactly as they do in the current Step 3.

#### 2.2 Fine-Tune Panel Expansion

The "Fine-tune assumptions" button toggles visibility of the configuration panel.

**Panel contents** (reusing existing components with wrapper adjustments):

1. **Scenario selector** (from `WizardOperatingStep`)
   - Dropdown: Baseline, Technology Breakthrough, Oil Crisis
   - Plain-language description below selection

2. **Purchase method** (from `WizardOperatingStep`)
   - Dropdown: Financed, Outright

3. **Duty cycle** (from `WizardOperatingStep`)
   - Pre-filled from the guided flow's driving pattern selection
   - Editable as percentage sliders or inputs
   - Real-time sum validation (must equal 100%)

4. **Cost adjustments** (from `WizardCostStep`, converted to percentage UI, see 2.3)

5. **Vehicle spec overrides** (from `VehicleParamsForm`)
   - Tucked into a collapsible sub-section: "Adjust vehicle specs"
   - Only shown for the currently active vehicles

6. **Add more trucks** button
   - Opens an "Add electric truck" dropdown (scoped to current weight class)
   - Functions like current Step 2's multi-select
   - New trucks added to `comparisonVehicles` array
   - Results recalculate reactively

**Behaviour:**
- On click: sets `showFineTune = true` in guided state, smooth-scrolls to panel.
- All changes trigger live recalculation (existing debounced reactive flow).
- Panel is collapsible.
- Emit `guided.fine_tune_opened` telemetry on first expand.

#### 2.3 Multiplier-to-Percentage Conversion

Replace all multiplier-based cost adjustment inputs with percentage-based display.

**Current UX (confusing):**
- Input label: "Diesel price adjustment"
- Input value: `1.10`
- Meaning: 10% higher than baseline

**New UX (clear):**
- Input label: "Diesel price"
- Display: `+10%` (or slider at +10% position)
- Subtext: "10% above today's price"

**Conversion logic:**

```typescript
// Percent to multiplier (for storage/calculator)
function percentToMultiplier(percent: number): number {
  return 1 + (percent / 100);
  // +10 -> 1.10, -15 -> 0.85, 0 -> 1.00
}

// Multiplier to percent (for display)
function multiplierToPercent(multiplier: number): number {
  return Math.round((multiplier - 1) * 100);
  // 1.10 -> +10, 0.85 -> -15, 1.00 -> 0
}
```

**Fields to convert:**

| Field | Current Input | New Display | Valid Range (%) |
|---|---|---|---|
| `fuel_price_variation` | 0.5 - 2.0 | -50% to +100% | -50 to +100 |
| `electricity_price_variation` | 0.5 - 2.0 | -50% to +100% | -50 to +100 |
| `residual_value_variation` | 0.5 - 1.5 | -50% to +50% | -50 to +50 |
| `maintenance_cost_variation` | 0.5 - 1.5 | -50% to +50% | -50 to +50 |
| `battery_life_variation` | 0.5 - 1.5 | -50% to +50% | -50 to +50 |
| `charging_efficiency_variation` | 0.7 - 1.3 | -30% to +30% | -30 to +30 |

**Implementation:** Create a `PercentAdjustInput` component that wraps the conversion. Internally stores the multiplier in the form, displays the percentage to the user. Slider or number input with +/- step buttons.

**Zod validation:** Keep existing multiplier ranges in the schema. The component converts at the boundary.

### Implementation Targets

| File | Action |
|---|---|
| `frontend/src/components/guided/FullBreakdownSection.tsx` | **New.** Wrapper that conditionally renders existing chart components. |
| `frontend/src/components/guided/FineTunePanel.tsx` | **New.** Wrapper that assembles existing config components with collapse behaviour. |
| `frontend/src/components/shared/PercentAdjustInput.tsx` | **New.** Percentage display component with multiplier conversion. |
| `frontend/src/utils/percentMultiplier.ts` | **New.** `percentToMultiplier` and `multiplierToPercent` helpers. |
| `frontend/src/components/wizard/WizardCostStep.tsx` | Modify to use `PercentAdjustInput` (or keep old version for legacy wizard route). |
| `frontend/src/components/wizard/WizardOperatingStep.tsx` | May need minor refactoring to work as a standalone panel (not just a wizard step). |
| `frontend/src/components/results/ResultsPanel.tsx` | No changes to rendering. May need prop to control "standalone" vs "embedded" layout. |

### Acceptance Criteria

- Users can complete the core guided flow (Path A or B to headline result) without seeing any advanced controls.
- "See full breakdown" expands the full chart suite inline. Charts render correctly with guided flow data.
- "Fine-tune assumptions" expands the config panel. All existing configuration options are accessible.
- All cost adjustment inputs display as percentages. "+10%" maps to multiplier 1.10 end-to-end.
- Baseline (0% / no change) is clearly marked on all adjustment inputs.
- Unit tests cover `percentToMultiplier` and `multiplierToPercent` with boundary values.
- Results update live as fine-tune inputs change.
- Calculator parity tests still pass (multiplier values unchanged internally).

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Incorrect percent-to-multiplier mapping silently skews results | Dedicated conversion helpers with exhaustive test matrix covering boundary values (-50%, 0%, +100%). |
| Existing wizard components may not render well outside the wizard form context | Test components in isolation. Create wrapper props for "standalone" mode if needed. |
| Two UIs for the same inputs (old wizard + new guided) creates maintenance burden | Feature flag. Plan to deprecate old wizard once guided flow is validated. |

---

## Phase 3: Recommendation Trust Layer

### Objective

Increase confidence in the recommendation and handle edge cases honestly. A user should understand *why* the tool is recommending what it recommends, and know when to take it with a grain of salt.

### User Stories Addressed

- New stories for feasibility, explainability, and negative-result framing (not in original UX-thinking stories, but flagged in Open Questions).

### Scope

#### 3.1 Feasibility Checks

Before or alongside the headline result, check for practical concerns:

| Check | Condition | User-facing message |
|---|---|---|
| **Range fit** | BEV `range_km` < user's `dailyKm` | "The [BEV model] has a range of Xkm, which is less than your typical Xkm/day. You may need to charge during the day." |
| **Payload gap** | BEV `payload` < diesel `payload` by > 10% | "The electric option carries about X tonnes less than your current truck. That might matter depending on your loads." |
| **Charging access** | Always shown (we can't infer this) | "This comparison assumes you can charge overnight at your depot. If you don't have depot charging yet, [costs may differ]." |

**Display:** Yellow info card below the headline, before the expansion buttons. Not blocking. Informational.

#### 3.2 "Why this recommendation" Explainer

A collapsible section below the headline result:

```
Why this comparison?

We matched your Hino 300 with the Jac N75 because they're in the same weight
class (Light Rigid) and are designed for similar work. The cost comparison uses
baseline fuel and electricity prices, a 15-year ownership period, and your
driving profile (150 km/day, mostly city).

All of these assumptions can be adjusted in "Fine-tune assumptions" below.
```

**Logic:** Template-based. Fill in: diesel model, BEV model, weight class, scenario, ownership period, daily km, driving pattern label. No AI generation.

#### 3.3 Confidence Indicator

A subtle badge on the headline result: "High confidence", "Medium confidence", or "Estimate".

| Level | Condition |
|---|---|
| High confidence | User provided daily km + driving pattern (or both match catalog defaults closely) |
| Medium confidence | User accepted defaults without adjustment |
| Estimate | Path B with "Not sure" selection |

**Display:** Small badge or label next to the headline savings figure. Tooltip explains what would increase confidence.

#### 3.4 Negative Outcome Framing

When diesel wins on total cost:

- Lead with the honest result: "Based on these assumptions, diesel costs about $X less over 15 years."
- Follow with constructive framing: "Electric gets closer under different conditions. Try the 'Technology Breakthrough' scenario to see how falling battery prices change the picture."
- Provide a one-click "Try this scenario" button that switches to tech breakthrough and recalculates.
- Never hide or downplay the diesel advantage. Trust is the product.

### Implementation Targets

| File | Action |
|---|---|
| `frontend/src/components/guided/FeasibilityChecks.tsx` | **New.** Yellow info cards for range, payload, charging warnings. |
| `frontend/src/components/guided/RecommendationExplainer.tsx` | **New.** Template-based "why this comparison" section. |
| `frontend/src/components/guided/ConfidenceBadge.tsx` | **New.** Badge component with tooltip. |
| `frontend/src/components/guided/HeadlineResult.tsx` | Extend with feasibility checks, explainer, confidence badge, and negative-outcome framing. |
| `frontend/src/utils/feasibility.ts` | **New.** Pure functions for range fit, payload gap, confidence level. |

### Acceptance Criteria

- Range warning appears when BEV range < daily km.
- Payload warning appears when BEV payload is > 10% less than diesel payload.
- Charging assumption note always appears (dismissable after first view).
- "Why this comparison" section is expandable and accurately reflects the user's selections.
- Confidence badge reflects whether user provided custom inputs or accepted defaults.
- When diesel is cheaper, the result is stated plainly with a constructive "try this scenario" action.
- All feasibility and confidence logic is deterministic and unit-tested.

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Over-warning reduces trust as much as under-warning | Keep warnings informational (yellow, not red). Max 2 warnings visible. Don't block the result. |
| "Try this scenario" could feel like the tool is pushing an agenda | Frame as exploration, not persuasion. "See how different assumptions change the picture." |
| Confidence levels are subjective | Start simple (3 levels). Tune thresholds with product review and telemetry data on user behaviour. |

---

## Phase 4: Data Enrichment for Better Matching

### Objective

Improve truck identification quality and visual appeal by enriching the vehicle catalog with metadata that helps users recognise their truck.

### User Stories Addressed

- **Story 10: Vehicle Catalog Enrichment** (full delivery)

### Scope

#### 4.1 Extended Vehicle Model

Add optional metadata fields to `VehicleModel` in the Python data layer:

```python
@dataclass(slots=True, frozen=True)
class VehicleModel:
    # Existing fields (unchanged)
    vehicle_id: str
    comparison_pair: str
    weight_class: str
    drivetrain_type: str
    model_name: str
    payload: float
    msrp: float
    range_km: float
    battery_capacity_kwh: float
    kwh_per_km: float
    litres_per_km: float
    battery_replacement_per_kw: float
    annual_registration: float
    annual_kms: float
    noise_pollution_per_km: float

    # New optional fields
    make: str = ""                    # "Hino", "Volvo", "Mercedes-Benz"
    model_variant: str = ""           # "300 Series", "FE", "Actros L"
    year_range: str = ""              # "2018-2025"
    gvw_range: str = ""               # "4.5t - 8.5t"
    body_types: tuple = ()            # ("cab chassis", "pantech", "tipper")
    common_uses: tuple = ()           # ("metro delivery", "furniture")
    aliases: tuple = ()               # ("Hino Dutro", "300 Series Wide Cab")
    image_url: str = ""               # URL to truck photo
```

#### 4.2 TypeScript Type Update

```typescript
// Additions to VehicleDetail in shared/types/tco.types.ts
interface VehicleDetail {
  // ... existing fields ...
  make?: string;
  model_variant?: string;
  year_range?: string;
  gvw_range?: string;
  body_types?: string[];
  common_uses?: string[];
  aliases?: string[];
  image_url?: string;
}
```

#### 4.3 Generation Script Update

Update `scripts/generate_vehicle_catalog_ts.py` to include new fields in the TypeScript output. Fields with empty/default values are omitted from the generated output to keep file size down.

#### 4.4 Guided Flow Enhancements

When enrichment data is available:
- **TruckSizeCards:** Show truck images instead of placeholder icons.
- **Model dropdown:** Show make and model variant for clearer identification.
- **WorkTypeCards:** Could show "common trucks for this work" using `common_uses` data.
- **Fuzzy matching (stretch):** If a user types "Dutro", `aliases` can match to Hino 300.

**Fallback:** When optional fields are absent, components render exactly as they do in Phase 1 (model_name + weight_class).

### Implementation Targets

| File | Action |
|---|---|
| `data/vehicles.py` | Extend `VehicleModel` with optional fields. Populate data for existing vehicles. |
| `scripts/generate_vehicle_catalog_ts.py` | Include new fields in generation. Omit empty values. |
| `shared/data/vehicleCatalog.ts` | Regenerated with enriched data. |
| `shared/types/tco.types.ts` | Add optional fields to `VehicleDetail`. |
| `frontend/src/components/guided/TruckSizeCards.tsx` | Use `image_url` when available. |
| `frontend/src/components/guided/WorkTypeCards.tsx` | Use `common_uses` when available. |

### Acceptance Criteria

- Enriched fields are present in generated TypeScript artifacts when populated in Python.
- Existing behaviour is unchanged when optional fields are absent (empty string / empty array defaults).
- Truck images display on size cards when `image_url` is provided.
- Model dropdown shows `make` + `model_variant` when available, falls back to `model_name`.
- No breaking changes to calculator or existing results components.

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Data quality varies across vehicles (some have images, some don't) | All fields optional. Explicit fallback copy/display for missing data. |
| Image hosting and loading performance | Use optimised images. Lazy-load with skeleton placeholder. Consider a CDN. |
| Aliases could create ambiguous matches | Only use aliases for display/search hints, not for automatic selection. |

---

## Phase 5: Rollout, Experimentation, and Optimisation

### Objective

Roll out the guided flow safely, measure its impact against the current wizard, and iterate based on observed user behaviour.

### Scope

#### 5.1 A/B Test Setup

- Feature flag controls traffic split: X% see guided flow, (100-X)% see current wizard.
- Both flows share the same calculator engine, so results are comparable.
- Track conversion funnel separately for each variant.

#### 5.2 Progressive Rollout

| Stage | Traffic | Duration | Gate |
|---|---|---|---|
| Internal / staging | 100% (team only) | 1 week | Functional QA pass |
| Canary | 10% of production traffic | 1-2 weeks | No critical errors, funnel metrics stable |
| Expanded | 50% | 2 weeks | Guided funnel >= wizard funnel on primary metrics |
| Full rollout | 100% | Ongoing | Guided flow is the default. Old wizard available at `/compare/classic`. |
| Deprecation | Remove old wizard | After 1 month at 100% | No regressions in any metric |

#### 5.3 Key Metrics

| Metric | What it tells us | Target |
|---|---|---|
| Entry fork selection split | Which path is more popular | Informational |
| Drop-off by guided step | Where users abandon | Lower than wizard step drop-off |
| Time to first result | How fast users get value | < 60 seconds |
| Headline result render rate | % of visitors who see a result | > 70% (vs wizard baseline) |
| Full breakdown open rate | Engagement with detail | > 30% of those who see headline |
| Fine-tune panel open rate | Power-user engagement | Informational (expect 10-20%) |
| Recalculation rate | Users exploring scenarios | Informational |
| Error rate in payload creation | Technical reliability | < 1% |

#### 5.4 Iteration Priorities

Based on telemetry, expected iteration areas:
- **Copy tweaks:** Adjust card labels, descriptions, and helper text based on where users hesitate.
- **Default tuning:** Adjust `WORK_TYPE_PROFILES` duty cycles and daily km defaults based on observed user overrides.
- **Path B "Not sure":** Determine whether 3-comparison view or single default performs better.
- **Mobile layout:** Optimise card sizes, scroll behaviour, and chart rendering for small screens.

### Acceptance Criteria

- Guided flow can be toggled on/off via feature flag with zero downtime.
- Both variants emit comparable telemetry events for funnel analysis.
- Rollback path is tested: flag flip returns 100% of traffic to current wizard within minutes.
- Guided flow outperforms baseline wizard on primary funnel metrics before expanding beyond 50%.
- No critical reliability regressions in any rollout stage.

---

## Cross-Cutting Engineering Work

### Testing Plan

#### Unit Tests
- `workTypeProfiles.ts`: Profile data integrity (duty cycles sum to 100, daily km > 0).
- `percentMultiplier.ts`: `percentToMultiplier` and `multiplierToPercent` with boundary values (-50%, 0%, +100%) and round-trip consistency.
- `feasibility.ts`: Range fit, payload gap, and confidence level with known vehicle pairs.
- `useGuidedFlow.ts`: Translation from guided state to `WizardData` for all path/selection combinations.
- `selectDefaultVehicles`: Correct vehicle pairs selected for each weight class and "not sure" case.

#### Integration Tests
- End-to-end Path A: entry fork -> size card -> model -> headline result.
- End-to-end Path B: entry fork -> work type -> headline result.
- Full breakdown expansion renders all charts without errors.
- Fine-tune panel changes trigger recalculation and update headline result.
- Fallback behaviour: missing comparison pair, empty weight class, etc.

#### Visual / Snapshot Tests
- Entry fork cards (desktop and mobile).
- Truck size cards (selected and unselected states).
- Headline result: savings positive, savings negative, loading state.
- Feasibility warning cards.

#### Regression Tests
- Existing calculator parity suite: within 5 cents for dollar amounts, 0.05 cents for cost_per_km.
- Current wizard route (`/compare`) continues to function identically when guided flow is enabled.

### Accessibility

- All cards are keyboard-navigable (`tabIndex`, `role="button"` or `<button>` elements).
- Clear focus-visible states on all interactive elements.
- Radio buttons use native `<input type="radio">` with proper `<label>` association.
- Colour is not the only indicator of state (selected cards have border + background change).
- Chart alt-text or `aria-label` describes the key finding.
- Mobile-first tap targets (minimum 44x44px).
- Screen reader announces dynamic content changes (headline result appearing, section expanding).

### Telemetry Events (Minimum Set)

```
guided.entry_viewed
guided.path_selected          { path }
guided.truck_size_selected    { weight_class }
guided.model_selected         { vehicle_id }
guided.work_type_selected     { work_type }
guided.daily_km_changed       { daily_km, annual_km }
guided.driving_pattern_selected { pattern }
guided.result_rendered        { diesel_id, bev_id, savings }
guided.full_breakdown_opened
guided.fine_tune_opened
guided.comparison_added       { vehicle_id }
guided.scenario_changed       { scenario }
guided.feasibility_warning_shown { warning_type }
```

---

## Go/No-Go Gates

| Gate | After Phase | Criteria |
|---|---|---|
| **A** | Phase 1 | Guided flow functionally complete. Both paths produce correct headline results behind feature flag. All calculator parity tests pass. |
| **B** | Phase 2 | Progressive disclosure working. Charts and fine-tune panel expand/collapse correctly. Multiplier-to-percent conversion verified end-to-end. |
| **C** | Phase 3 | Trust layer in place. Feasibility checks, explainer, and negative-outcome framing reviewed by product/domain team. |
| **D** | Phase 5 start | Guided flow outperforms wizard baseline on headline-result render rate before traffic expands beyond 50%. |

## Out of Scope for Initial Launch

- Full fuzzy text search for truck matching (requires search infrastructure).
- Shareable / public result URLs (requires backend route + OG metadata).
- AI assistant or conversational onboarding.
- Mandatory backend schema changes for enriched vehicle metadata (Phase 4 is additive).
- PDF export of results.
- User accounts or saved comparisons across devices.

## Story-to-Phase Mapping

| Story | Phase | Status |
|---|---|---|
| Story 1: Entry Point Fork | Phase 1 | |
| Story 2: Truck Identification (Path A) | Phase 1 | |
| Story 3: Usage Profile (Path A) | Phase 1 | |
| Story 4: Work Type Selection (Path B) | Phase 1 | |
| Story 5: Instant Headline Result | Phase 1 | |
| Story 6: Full Breakdown (Expandable) | Phase 2 | |
| Story 7: Fine-Tune Panel (Expandable) | Phase 2 | |
| Story 8: Multiplier-to-Percentage Translation | Phase 2 | |
| Story 9: Work-Type Profile Data | Phase 0 | |
| Story 10: Vehicle Catalog Enrichment | Phase 4 | |
