# UX Redesign: Guided Truck Cost Comparison

## The Problem

The current wizard assumes the user already knows what they want to compare. It asks for weight classes, vehicle IDs, duty cycle percentages, and multiplier-based cost adjustments. That works for fleet analysts. It doesn't work for a sub-contractor driving a Hino 300 who's heard electric trucks might save them money and wants to find out.

The target user:
- Knows their truck by make and model, not by weight class
- Thinks in "kilometres per day" and "dollars per week on diesel", not annual kms and fuel price variation multipliers
- Wants an answer ("will I save money?") before they're willing to invest effort in configuration
- May not own a truck yet and is trying to figure out what to buy

## Design Principles

1. **Answer first, configure later.** Show a headline result within 2-3 clicks. Let people refine from there.
2. **Plain language.** "How far do you drive each day?" not "Annual kilometres." No multipliers. No jargon.
3. **Smart defaults over empty forms.** If we can infer it, don't ask for it.
4. **Progressive disclosure.** Spec overrides, scenario modelling, and sensitivity analysis exist for power users, behind a "Fine-tune" panel.
5. **One recommendation, not a comparison grid.** For the default flow, suggest the single best electric match. Let power users add more.

---

## Vehicle Catalog: Current State

The catalog currently has **16 vehicles** (8 BEV, 8 Diesel) across 3 weight classes:

| Weight Class | Diesel Models | BEV Models |
|---|---|---|
| Light Rigid | Hino 300, Hyundai Mighty, Hino 500 | Jac N75, Hyundai Mighty Electric, Jac N90 |
| Medium Rigid | Volvo FE, MB Actros | Volvo FL, MB eActros 300 |
| Articulated | MB Actros, Volvo FH, Scania R560 | MB eActros 600, Volvo FH, Scania 45R |

Every vehicle has a `comparison_pair` linking it to its diesel/BEV counterpart. This is the backbone of the guided experience: if we can identify the user's diesel truck, we can auto-select the best electric comparison.

---

## The New User Journey

### Entry Point: "Do you have a truck?"

A single fork on the landing screen. Two large, tappable cards. No dropdowns, no forms.

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

Both paths converge at the same results view. The difference is how we gather enough information to populate the calculation.

---

### Path A: "I have a truck"

#### A1. What do you drive? (1 screen, ~10 seconds)

**What the user sees:**

Three large visual cards for weight class, using photos and plain language. No dropdowns yet.

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

**Why this works:** Drivers recognise their truck by size and by the names listed. Weight class labels ("Light Rigid") can appear as a subtle subtitle, but the primary label is conversational.

**On selection:** The card highlights and a dropdown appears below it showing the specific models in that class.

#### A2. Pick your model (inline, ~5 seconds)

A short dropdown with 2-3 models, scoped to the weight class they selected. Each option shows model name and a one-line summary:

```
Which model is closest to yours?

  Hino 300         ~4.5t payload, ~$80k
  Hyundai Mighty   ~4t payload, ~$75k
  Hino 500         ~6t payload, ~$130k
```

**Fallback if their exact truck isn't listed:** A note below the dropdown: "Don't see your truck? Pick the closest match by payload. You can fine-tune the specs later."

#### A3. How do you use it? (inline, ~15 seconds)

Two plain-language questions appear below the model selection. No new page.

```
Roughly how far do you drive on a typical day?
+--------------------------------------+
|  [  150  ] km/day                    |
|  That's about 36,000 km/year         |
+--------------------------------------+

What kind of driving do you mostly do?
  * Mostly city / metro deliveries        -> sets 80/15/5
  * Mix of city and regional              -> sets 50/35/15
  * Mostly regional / inter-city          -> sets 15/60/25
  * Long haul / interstate                -> sets 5/15/80
```

**What happens behind the scenes:**
- Daily km input is multiplied by ~240 working days to get annual kms
- The radio button maps to a duty cycle preset (shown above)
- These are stored as the same `dutyCycle` and `annual_kms` fields the calculator already expects

**Fallback:** If we wanted to avoid even these questions, we could use the catalog defaults (23,000 km/year for rigids, 84,000 for artics) and a "mixed" duty cycle. The user could adjust later.

#### A4. Your comparison (instant result)

This is the payoff. One screen. Appears immediately after they answer the two questions above (or auto-loads with defaults if they skip).

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

**What "See full breakdown" opens:** The existing charts (cost per km, cost components, payback timeline, sensitivity). Same ResultsPanel, just gated behind a click.

**What "Fine-tune assumptions" opens:** The existing ComparisonConfigPanel (scenarios, duty cycle sliders, cost adjustments, vehicle spec overrides). Same components, just collapsed by default.

---

### Path B: "I'm looking to buy"

#### B1. What kind of work? (1 screen, ~10 seconds)

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

**Mapping logic:**

| Selection | Inferred weight class | Duty cycle | Daily km default |
|---|---|---|---|
| Local deliveries | Light Rigid | 80/15/5 | 100 km |
| Regional freight | Medium Rigid | 15/60/25 | 200 km |
| Interstate / long haul | Articulated | 5/15/80 | 350 km |
| Not sure | Show all 3 weight classes side by side | 50/35/15 | 150 km |

#### B2. How far each day? (inline, ~5 seconds)

Same daily-km input as Path A, Step A3. Pre-filled with the default from the mapping above. User can adjust or skip.

```
How far would you typically drive in a day?
+--------------------------------------+
|  [  200  ] km/day                    |
|  That's about 48,000 km/year         |
+--------------------------------------+
```

#### B3. Your options (instant result)

For Path B, we show diesel vs electric side by side for the recommended weight class, using the catalog's `comparison_pair` to pick the match. If they selected "Not sure", show all three weight classes in tabs or cards.

```
+-------------------------------------------------------------+
|                                                             |
|  For regional freight, here's a typical comparison:         |
|                                                             |
|  +--------------------+  vs  +----------------------+      |
|  |  Volvo FE           |     |  Volvo FL (Electric)  |      |
|  |  Diesel             |     |                       |      |
|  |  ~$220,000          |     |  ~$200,000            |      |
|  |  12t payload        |     |  10.5t payload        |      |
|  |  $X.XX / km         |     |  $X.XX / km           |      |
|  |  $XXX,XXX total     |     |  $XXX,XXX total       |      |
|  +--------------------+      +----------------------+       |
|                                                             |
|  The electric option could save you $XX,XXX over 15 years   |
|                                                             |
|  [See full breakdown]     [Compare more trucks]             |
|                                                             |
+-------------------------------------------------------------+
```

**"Compare more trucks"** opens the existing multi-select flow from the current Step 2, but now the user arrives with context and a recommendation rather than a blank slate.

---

## How Both Paths Converge

After the quick result, both paths offer the same two expansion routes:

### Expansion 1: Full Breakdown (current ResultsPanel)
- Cost per km chart
- Cost component breakdown
- Payback timeline
- Savings waterfall
- Sensitivity tornado

### Expansion 2: Fine-Tune (current ComparisonConfigPanel + VehicleParamsForm)
- Scenario selection (baseline / tech breakthrough / oil crisis)
- Purchase method (financed / outright)
- Duty cycle sliders (pre-filled from their earlier answer)
- Cost adjustments (but as percentages, not multipliers: "+10% diesel price" not "1.10")
- Vehicle spec overrides
- Add/remove comparison vehicles

The key change: these panels start **collapsed**. The user got their answer. Now they're choosing to dig deeper because they're interested, not because the tool demanded it.

---

## Data Requirements

### Optimal: Richer Vehicle Identification

To support "what do you drive?" with real confidence, the catalog would benefit from:

| New Field | Purpose | Example Values |
|---|---|---|
| `make` | Manufacturer (separate from model) | "Hino", "Volvo", "Mercedes-Benz" |
| `model` | Specific model name | "300 Series", "FE", "Actros" |
| `body_types` | What configurations this truck comes in | ["cab chassis", "pantech", "tipper", "tautliner"] |
| `gvw_range` | Gross vehicle weight range | "4.5t - 8.5t" |
| `common_uses` | Typical applications | ["metro delivery", "furniture", "food distribution"] |
| `year_range` | Model years this data applies to | "2018-2025" |
| `aliases` | Common alternative names drivers might use | ["Hino Dutro", "300 Series Wide Cab"] |
| `image_url` | Photo for visual recognition | URL to truck image |

This would allow fuzzy matching: "I drive a Dutro" maps to Hino 300. "I do furniture deliveries" maps to Light Rigid.

### Minimum Viable: Use What Exists

The current catalog already has enough to build the guided flow:

- `model_name` + `weight_class` gives us the selection cards in Path A
- `comparison_pair` gives us the auto-matched electric recommendation
- `payload` and `msrp` give us the summary info on each card
- Weight class maps cleanly to the "work type" cards in Path B

**The main gap:** We'd be mapping work types to weight classes with a hardcoded lookup table rather than data-driven matching. That's fine for 3 weight classes. It would break down with a larger, more nuanced catalog.

### Recommended: Add a Work-Type Mapping Layer

A lightweight middle ground. Add a `workTypeProfiles` data structure:

```typescript
const WORK_TYPE_PROFILES = {
  local_delivery: {
    label: "Local deliveries",
    description: "Food, parcels, furniture, retail",
    recommended_weight_class: "Light Rigid",
    default_daily_km: 100,
    duty_cycle: { urban: 80, regional: 15, longHaul: 5 },
  },
  regional_freight: {
    label: "Regional freight",
    description: "Between cities within a state",
    recommended_weight_class: "Medium Rigid",
    default_daily_km: 200,
    duty_cycle: { urban: 15, regional: 60, longHaul: 25 },
  },
  interstate: {
    label: "Interstate / long haul",
    description: "Capital to capital, cross-state",
    recommended_weight_class: "Articulated",
    default_daily_km: 350,
    duty_cycle: { urban: 5, regional: 15, longHaul: 80 },
  },
  mixed: {
    label: "Mixed / not sure",
    description: "Show me all the options",
    recommended_weight_class: null, // show all
    default_daily_km: 150,
    duty_cycle: { urban: 50, regional: 35, longHaul: 15 },
  },
} as const;
```

This is maintainable, testable, and keeps the mapping logic out of UI components.

---

## User Stories

### Epic: Guided Quick Comparison

> As a truck driver or sub-contractor with limited financial experience, I want to find out whether an electric truck would save me money, without needing to understand weight classes, duty cycles, or cost multipliers.

#### Story 1: Entry Point Fork
**As a** visitor to the site
**I want to** immediately see two clear options: "I have a truck" or "I'm looking to buy"
**So that** I'm guided down the right path without having to figure out the tool

**Acceptance criteria:**
- Landing screen shows two large, tappable cards
- No other form fields, dropdowns, or configuration visible
- Cards use plain language and a brief description of who each path is for
- Selecting a card navigates to the appropriate guided flow
- Mobile-friendly: cards stack vertically on small screens

---

#### Story 2: Truck Identification (Path A)
**As a** driver who owns a diesel truck
**I want to** identify my truck by recognising its size and model name
**So that** the tool can find the right comparison without me knowing technical classifications

**Acceptance criteria:**
- Three visual cards represent the weight classes using photos, plain-English labels ("Small truck", "Medium truck", "Semi / prime mover"), and example model names
- Selecting a card reveals a short dropdown of specific diesel models in that class
- Each dropdown option shows model name, approximate payload, and price
- A note below the dropdown says: "Don't see your truck? Pick the closest match. You can adjust the specs later."
- Selection sets `currentVehicle` in the store and auto-selects the `comparison_pair` BEV

---

#### Story 3: Usage Profile (Path A)
**As a** driver who has identified their truck
**I want to** describe how I use my truck in everyday terms
**So that** the cost comparison reflects my actual situation

**Acceptance criteria:**
- A daily-km number input with live conversion to annual kms shown below ("That's about X km/year")
- Annual kms calculated as: daily input x 240 working days (configurable constant)
- Four radio-button options for driving pattern, each mapping to a duty cycle preset
- Radio labels use plain language ("Mostly city / metro deliveries") not percentages
- Both fields appear inline below the truck selection, not on a separate page
- Sensible defaults pre-filled (catalog's `annual_kms` converted to daily, "Mix of city and regional" selected)

---

#### Story 4: Work Type Selection (Path B)
**As a** prospective truck buyer
**I want to** describe the kind of work I'll be doing
**So that** the tool can recommend appropriate trucks to compare

**Acceptance criteria:**
- Four visual cards: Local deliveries, Regional freight, Interstate/long haul, Not sure
- Each card has a 1-line description of typical cargo or routes
- Selecting a card sets the recommended weight class, duty cycle preset, and default daily kms from `WORK_TYPE_PROFILES`
- Daily-km input appears below (pre-filled with profile default, editable)
- "Not sure" shows a comparison across all weight classes (tabs or stacked cards)

---

#### Story 5: Instant Headline Result
**As a** user who has completed either path (A or B)
**I want to** immediately see whether electric would save me money
**So that** I get value from the tool before being asked to configure anything else

**Acceptance criteria:**
- Result appears on the same page, below the inputs (no navigation required)
- Headline shows: savings amount (lifetime), savings per year, and savings per km
- If electric is more expensive, say so honestly: "Based on these assumptions, diesel costs less over 15 years. But here's what could change that..." (link to scenarios)
- Two summary cards show diesel vs electric: cost per km, total cost
- Two action buttons: "See full breakdown" and "Fine-tune assumptions"
- Calculation runs client-side using existing calculator engine
- Loading state: spinner with "Crunching the numbers..." (sub-second expected)

---

#### Story 6: Full Breakdown (Expandable)
**As a** user who saw the headline and wants to understand the detail
**I want to** see the full cost breakdown, payback timeline, and sensitivity analysis
**So that** I can build confidence in the comparison before making a decision

**Acceptance criteria:**
- "See full breakdown" expands or scrolls to the existing chart suite
- Charts shown: cost per km, cost components, payback timeline, savings waterfall, sensitivity tornado
- All charts use the selections from the guided flow (no re-entry required)
- Section can be collapsed again
- On mobile: charts stack full-width and are swipeable or scrollable

---

#### Story 7: Fine-Tune Panel (Expandable)
**As a** user who wants to explore different assumptions
**I want to** adjust cost inputs, scenarios, and vehicle specs
**So that** I can model my specific situation more precisely

**Acceptance criteria:**
- "Fine-tune assumptions" expands a panel with the existing configuration options
- Duty cycle pre-filled from the guided flow selection (editable as sliders or percentage inputs)
- Cost adjustments presented as percentages ("+10% diesel price") not multipliers (1.10)
- Scenario selector with plain-language descriptions
- Vehicle spec overrides available but tucked into a sub-section ("Adjust vehicle specs")
- Option to add more electric trucks for comparison ("Compare another electric truck")
- Results update live as the user adjusts (existing reactive calculation behaviour)
- Panel can be collapsed again

---

#### Story 8: Multiplier-to-Percentage Translation
**As a** user adjusting cost assumptions
**I want to** enter percentage changes ("+10%", "-15%") instead of decimal multipliers
**So that** I don't have to mentally convert between "0.90" and "10% lower"

**Acceptance criteria:**
- All adjustment inputs display as percentage offsets from baseline: "-10%", "+20%", "0%" (no change)
- Internally, values are still stored as multipliers for calculator compatibility
- A slider or +/- stepper control could replace the raw number input
- Baseline (0% / 1.0x) is clearly marked
- Input labels describe the effect: "Diesel price: +10% above today's price"

---

### Epic: Data Layer Enhancements

#### Story 9: Work-Type Profile Data
**As a** developer building the guided flow
**I need** a structured mapping from work types to vehicle recommendations and operating defaults
**So that** Path B can infer weight class, duty cycle, and daily kms from a single selection

**Acceptance criteria:**
- `WORK_TYPE_PROFILES` constant defined in shared/data
- Each profile contains: label, description, recommended_weight_class (nullable), default_daily_km, duty_cycle
- Profiles used by Path B selection cards and by Path A radio buttons
- Generated from Python data layer (like other shared constants) or manually maintained with clear documentation

---

#### Story 10: Vehicle Catalog Enrichment (Future)
**As a** user trying to identify their truck
**I want** the catalog to include make, body type, and common use descriptions
**So that** fuzzy matching and visual identification work even if I don't know the exact model name

**Acceptance criteria:**
- `VehicleModel` extended with optional fields: `make`, `body_types`, `common_uses`, `gvw_range`, `year_range`, `aliases`, `image_url`
- Fields are optional to avoid breaking existing data
- Generation script updated to include new fields in TypeScript output
- Landing flow can display images and filter by use case when data is available
- Fallback: when fields are missing, the current model_name + weight_class display is used

---

## Screen Flow Summary

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

## Click Counts to Insight

| Path | Clicks to headline result | What the user did |
|---|---|---|
| A (owns truck) | 3-4 | Size card, model dropdown, daily km + driving pattern, [auto-calculates] |
| A (skip optional) | 2 | Size card, model dropdown [uses defaults, auto-calculates] |
| B (buying) | 2-3 | Work type card, daily km adjust (optional), [auto-calculates] |
| B (not sure) | 1 | "Not sure" card [shows all classes with defaults] |
| Current wizard | 6+ | Diesel dropdown, next, electric dropdown, next, scroll past config to see results |

## Migration Strategy

This isn't a rewrite. The new flow is a **new entry layer** that feeds into the existing calculator and results components.

### What stays the same
- Calculator engine (shared/calculator)
- Results components (ResultsPanel, all charts)
- Configuration components (ComparisonConfigPanel, VehicleParamsForm, WizardCostStep)
- State shape (WizardData in Zustand store)
- Calculation hook (useCalculations)

### What changes
- WizardPage.tsx replaced with a new GuidedFlowPage (or refactored in place)
- WizardStepper removed (no numbered steps in the guided flow)
- WizardDieselStep and WizardElectricStep replaced with the guided selection components
- WizardCompareStep refactored: results shown inline, config panels collapsed by default
- New components: EntryForkCards, TruckSizeCards, WorkTypeCards, DailyKmInput, DrivingPatternRadio, HeadlineResult
- New data: WORK_TYPE_PROFILES constant
- Cost adjustment inputs converted from multiplier to percentage display

### What can wait
- Vehicle catalog enrichment (make, body_types, images) (Story 10)
- Fuzzy search / "type your truck" free-text input
- Onboarding tooltips or walkthrough
- Shareable result URLs

## Open Questions

1. **Working days constant:** 240 days/year is a reasonable default for daily-to-annual km conversion. Should this be configurable, or is a fixed constant fine?

2. **"Not sure" path:** When the user picks "Not sure" in Path B, do we show 3 separate comparisons (one per weight class), or pick a single "middle of the road" default (Medium Rigid)?

3. **Negative result framing:** When diesel wins on cost, how much do we editorialize? Options range from neutral ("Diesel costs $X less over 15 years under these assumptions") to constructive ("Diesel costs less today, but electric closes the gap under a technology breakthrough scenario. [Try it]").

4. **Single-page vs multi-page:** The flow above is designed as a single scrolling page with progressive sections. An alternative would be animated card transitions (like a mobile onboarding flow). Which feels more appropriate for the audience?

5. **Should Path A allow skipping the usage questions entirely?** We could auto-calculate with defaults the moment they pick a model, and show the usage questions as part of "Fine-tune" instead. That gets to a result in 2 clicks.
