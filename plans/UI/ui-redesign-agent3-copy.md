# Agent 3: Copy & Content Simplification

## Context
You are one of three Opus 4.5 sub-agents working in parallel on a UI/UX redesign of the MyBuild TCO Calculator. This is a React/TypeScript app for fleet operators comparing diesel vs electric trucks.

**Your focus**: Simplifying UI copy, labels, hints, and terminology
**Other agents (DO NOT TOUCH THEIR FILES):**
- Agent 1: Config files, CSS, shared components (Card, Button, Field, Select, AppShell, WizardStepper)
- Agent 2: Chart components (CostPerKmChart, CostBreakdownChart, PaybackChart, etc., ResultsPanel)

## Core Principle
Make language accessible to non-technical fleet operators. Remove jargon, use plain English, focus on what users need to know.

## CRITICAL: Do NOT Modify
- Any files in `frontend/src/state/`
- Any files in `frontend/src/hooks/`
- Any files in `frontend/src/services/calculator/`
- `frontend/src/utils/payload.ts`
- Validation LOGIC in `wizardForm.ts` (only change display strings)

## Terminology Glossary (Apply Everywhere)
| Avoid | Use Instead |
|-------|-------------|
| BEV | electric truck |
| Vehicle | truck |
| Baseline | your current truck |
| Trajectory | trend / outlook |
| Multiplier | adjustment |
| PV / Present Value | total |
| Spec sheet | specifications |
| Duty cycle | route mix |
| MSRP | purchase price |
| Override | adjust / custom value |

---

## Your Files to Modify

### 1. frontend/src/pages/WizardPage.tsx
**Step titles and descriptions:**

| Location | Before | After |
|----------|--------|-------|
| Step 1 title | "Your diesel truck" | "Your current truck" |
| Step 1 description | "Choose the baseline vehicle you operate today." | "Select the truck you want to compare." |
| Step 2 title | "Electric alternatives" | "Electric options" |
| Step 2 description | "Pick BEVs in the same class and edit their specs." | "Choose electric trucks to compare." |
| Step 3 title | "Configure & compare" | "See your results" |
| Step 3 description | "View results and explore scenarios." | "Compare costs and adjust assumptions." |

**Toast/validation messages:**
| Before | After |
|--------|-------|
| "Select at least one vehicle to continue." | "Select a truck to continue." |
| "Comparison saved to your session." | "Results saved." |
| "Calculation failed. Please try again." | "Something went wrong. Try again or refresh the page." |

### 2. frontend/src/components/wizard/WizardDieselStep.tsx
**Labels and text:**
| Before | After |
|--------|-------|
| Card title "Step 1 - Current diesel" | "Your current truck" |
| "Pick the diesel truck you operate today, or the closest alternative." | "Choose the diesel truck you're running now. We'll use this as your baseline for comparison." |
| "Diesel model" (select label) | "Select your truck" |
| "Filtered to diesel models only..." (hint) | Remove entirely |
| "Select a diesel above to see details." | "Select a truck to see its specifications." |
| "MSRP" | "Purchase price" |
| "Weight class" | "Size class" |
| "Diesel assumptions & overrides" | "Adjust specifications" |

### 3. frontend/src/components/wizard/WizardElectricStep.tsx
**Labels and text:**
| Before | After |
|--------|-------|
| Card title "Step 2 - Electric Alternatives" | "Electric trucks to compare" |
| "Filtered to {class} BEVs so you can compare like-for-like." | "Showing {class} electric trucks so you can make a fair comparison." |
| "Select a diesel first to unlock the filtered BEV list." | "Go back and select your current truck first." |
| "Add BEV alternative" | "Add an electric truck" |
| "You can add multiple BEVs - each will show up as a chip below." | "Add as many as you'd like to compare." |
| "+ Add suggested pair: {name}" | "+ Add recommended match: {name}" |
| "Selected BEVs" | "Trucks you're comparing" |
| "No BEVs selected yet." | "No electric trucks selected yet." |
| "Override default assumptions" | "Adjust specifications" |

### 4. frontend/src/components/wizard/WizardOperatingStep.tsx
**This file has the most jargon - simplify heavily:**

| Before | After |
|--------|-------|
| Card title "Operating profile" | "How you use your trucks" |
| "Scenarios and duty-cycle assumptions that drive the lifetime cost calculation." | "Tell us about your typical operations so we can estimate costs accurately." |
| "Scenario trajectory" | "Market scenario" |
| "Pulls trajectories from the pre-configured scenarios." | "Choose how you think fuel and energy prices will change over time." |
| "Purchase method" | "How will you buy?" |
| "Detemines pricing approach." | "Financing adds interest costs but spreads payments over time." (also fix typo) |
| "Duty-cycle mix" section title | "Your typical routes" |
| "Percent of annual kilometres by route type. Must add up to 100%." | "What percentage of your driving is on each route type? (Must total 100%)" |
| "Urban (%)" | "City/metro" |
| "Regional (%)" | "Regional roads" |
| "Long haul (%)" | "Highway/long distance" |
| "Annual kilometres" | "Kilometres per year" |
| "Override default kms for the selected vehicles." | "Leave blank to use the truck's typical annual distance." |
| "Residual value multiplier" | "Resale value adjustment" |
| "0.9 reduces resale expectations by 10%." | "Values below 1.0 reduce expected resale; above 1.0 increases it." |
| "Maintenance multiplier" | "Maintenance cost adjustment" |
| "Increase/decrease maintenance costs globally." | "Adjust if you expect higher or lower maintenance costs than typical." |

### 5. frontend/src/components/wizard/WizardCostStep.tsx
**Labels and hints:**
| Before | After |
|--------|-------|
| Card title "Cost sensitivity" | "Price adjustments" |
| "Optional multipliers for quick scenario exploration." | "Adjust fuel and energy prices to test different assumptions." |
| "Diesel $ multiplier" | "Diesel price adjustment" |
| "1.12 represents a 12% diesel price increase across the life of the vehicle." | "Enter 1.10 for 10% higher prices, 0.90 for 10% lower." |
| "Electricity $ multiplier" | "Electricity price adjustment" |
| "Apply shocks or savings to the energy price trajectory." | "Enter 1.10 for 10% higher prices, 0.90 for 10% lower." |
| "Battery multiplier" | "Battery life adjustment" |
| "0.7 shortens life (higher replacement cost), 1.2 extends it." | "Lower values mean batteries wear out faster; higher values mean they last longer." |
| "Charging efficiency multiplier" | "Charging efficiency" |
| "Impacts BEV charging energy required per kilometre." | "Higher values mean the truck uses more energy while charging." |

### 6. frontend/src/components/wizard/VehicleParamsForm.tsx
**Labels and hints:**
| Before | After |
|--------|-------|
| "Overrides are optional - leave blank to use defaults." | "Optional - leave blank to use standard values." |
| "Select a vehicle to unlock parameter edits." | "Select a truck to adjust its specifications." |
| "No vehicle selected yet." | "No truck selected." |
| "Spec sheet missing for {id}." | "We don't have specifications for this truck." |
| "Reset to defaults" | "Reset all" |
| "MSRP (A$)" | "Purchase price ($)" |
| "Payload (t)" | "Payload capacity (tonnes)" |
| "Annual Rego (A$)" | "Registration cost ($/year)" |
| "Interest Rate (%)" | "Loan interest rate" |
| "Absolute annual rate - e.g. 0.06 for 6%." | "Enter as a decimal: 0.06 = 6% per year" |
| "Litres per km" | "Fuel consumption (L/km)" |
| "Battery capacity (kWh)" | "Battery size (kWh)" |
| "kWh per km" | "Energy consumption (kWh/km)" |
| "Charging Time (hours)" | "Charge time (hours)" |
| "Overrides the class-average charging duration." | "How long a full charge takes at your depot." |

### 7. frontend/src/components/results/ComparisonHighlights.tsx
**Results copy:**
| Before | After |
|--------|-------|
| Card title "Highlights" | "Key findings" |
| "Key takeaways from the latest comparison run." | "Summary of your comparison results." |
| "Winner" badge | "Lowest cost" |
| "Best option" | "Most cost-effective" |
| "Lifetime PV {amount}" | "Total cost: {amount}" |
| "Cost gap to baseline" | "Savings vs your current truck" |
| "Diesel is still optimal" | "Your diesel is cheapest" |
| "Your current truck already leads this scenario." | "Under these assumptions, keeping your diesel truck costs less." |
| "{savings} Savings compared to {baseline}." | "You'd save {savings} compared to your current truck." |
| "Annual delta {amount} saved each year." | "That's {amount} per year." |
| "Cost gap" | "Gap to second place" |
| "Add another vehicle" | "Add more trucks to compare" |
| "{name} is higher over the horizon." | "{name} costs {amount} more over the truck's lifetime." |
| "Select at least one comparator to quantify the gap." | "Add another truck to see how they compare." |

### 8. frontend/src/forms/wizardForm.ts
**Scenario labels and descriptions (DO NOT change validation logic):**

| Before | After |
|--------|-------|
| Scenario label "Baseline" | "Current trends" |
| Description "Steady 2-3% fuel escalators, moderate maintenance curve, current battery pricing." | "Fuel prices rise steadily (2-3%/year), battery costs continue their current decline." |
| Scenario label "Technology breakthrough" | "Fast EV progress" |
| Description "Faster battery cost decline, improved BEV efficiency, maintenance advantage extends." | "Battery costs drop faster, electric trucks become more efficient and cheaper to maintain." |
| Scenario label "Oil crisis" | "High fuel prices" |
| Description "Diesel price spike in year 3 and beyond, higher volatility, electricity steady at +3% per year." | "Diesel prices spike after 3 years; electricity prices stay stable at +3%/year." |

**Validation error messages (if customizable):**
| Before | After |
|--------|-------|
| "Urban % must be a number." | "Enter a number for city/metro percentage." |
| "Cannot be negative." | "Must be 0 or higher." |
| "Cannot exceed 100%." | "Can't be more than 100%." |
| "Duty cycle must add up to 100%." | "Route percentages must total 100%." |
| "Minimum 5,000 km per year." | "Enter at least 5,000 km per year." |

---

## Testing Checklist
1. All "BEV" replaced with "electric truck"
2. All "vehicle" replaced with "truck" (where referring to the user's trucks)
3. No unexplained jargon remains
4. Hints actually help users make decisions
5. Error messages are clear and actionable
6. Run `bun test` to ensure no regressions
7. Read through the wizard flow - does it make sense to a non-technical user?
